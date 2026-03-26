#!/usr/bin/env python3
"""Parallel dispatch runner for Codex CLI subagents.

Reads a JSON manifest of tasks, launches them as parallel Codex CLI
invocations, and writes structured artifacts + a summary JSON to stdout.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any

# ---------------------------------------------------------------------------
# Task type configuration -- single source of truth
# ---------------------------------------------------------------------------

TYPE_CONFIG: dict[str, dict[str, str]] = {
    "review":    {"sandbox": "read-only",       "effort": "high"},
    "analyze":   {"sandbox": "read-only",       "effort": "high"},
    "search":    {"sandbox": "read-only",       "effort": "high"},
    "document":  {"sandbox": "read-only",       "effort": "high"},
    "implement": {"sandbox": "workspace-write", "effort": "xhigh"},
    "refactor":  {"sandbox": "workspace-write", "effort": "xhigh"},
    "debug":     {"sandbox": "workspace-write", "effort": "xhigh"},
    "architect": {"sandbox": "workspace-write", "effort": "xhigh"},
}
DEFAULT_CONFIG: dict[str, str] = {"sandbox": "read-only", "effort": "high"}

MAX_OUTPUT_BYTES = 10 * 1024  # 10 KB cap for summary output field
SAFE_PATH_COMPONENT_RE = re.compile(r"^[A-Za-z0-9._-]+$")

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _die(msg: str) -> None:
    print(msg, file=sys.stderr)
    sys.exit(2)


def _get_repo_root(start_path: str) -> str:
    if os.path.isfile(start_path):
        repo_probe_cwd = os.path.dirname(os.path.abspath(start_path)) or "."
    else:
        repo_probe_cwd = os.path.abspath(start_path) or "."

    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            cwd=repo_probe_cwd,
        )
    except OSError as exc:
        _die(f"Failed to detect git repo root: {exc}")

    if result.returncode != 0:
        _die(f"Failed to detect git repo root: {result.stderr.strip()}")
    return result.stdout.strip()


def _validate_path_component(value: str, label: str) -> str:
    if value in {".", ".."} or SAFE_PATH_COMPONENT_RE.fullmatch(value) is None:
        raise ValueError(
            f"{label} {value!r} must contain only letters, numbers, '.', '_' or '-'."
        )
    return value


def _git_changed_files(cwd: str) -> list[str]:
    """Return changed and untracked file names in *cwd* via ``git status --porcelain=v1 -z``."""
    result = subprocess.run(
        ["git", "status", "--porcelain=v1", "-z"],
        capture_output=True,
        cwd=cwd,
    )
    if result.returncode != 0:
        return []

    entries = result.stdout.split(b"\0")
    files: set[str] = set()
    idx = 0
    while idx < len(entries):
        entry = entries[idx]
        idx += 1
        if not entry:
            continue

        status = entry[:2].decode("utf-8", errors="replace")
        path_part = entry[3:]
        if status.startswith(("R", "C")):
            if idx >= len(entries):
                break
            idx += 1

        if path_part:
            files.add(path_part.decode("utf-8", errors="replace"))

    return sorted(files)


def _read_task_meta(artifact_dir: str, task_id: str) -> dict[str, Any] | None:
    meta_path = os.path.join(artifact_dir, task_id, "meta.json")
    try:
        with open(meta_path, encoding="utf-8") as f:
            meta = json.load(f)
    except (OSError, json.JSONDecodeError):
        return None

    return meta if isinstance(meta, dict) else None


# ---------------------------------------------------------------------------
# Pre-flight checks
# ---------------------------------------------------------------------------


def preflight() -> None:
    if shutil.which("codex") is None:
        _die("Error: 'codex' not found on PATH. Install Codex CLI first.")

    try:
        result = subprocess.run(
            ["codex", "login", "status"],
            capture_output=True,
            text=True,
        )
    except OSError as exc:
        _die(
            f"Error: Failed to execute 'codex' binary found on PATH: {exc}. "
            "Check file permissions and binary format."
        )
    if result.returncode != 0:
        _die("Error: Codex auth check failed. Run 'codex login' to authenticate.")


# ---------------------------------------------------------------------------
# Manifest loading & validation
# ---------------------------------------------------------------------------


def load_manifest(path: str) -> list[dict[str, Any]]:
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, json.JSONDecodeError) as exc:
        _die(f"Error reading manifest: {exc}")

    if not isinstance(data, dict) or "tasks" not in data:
        _die("Manifest must contain a top-level 'tasks' array.")

    tasks = data["tasks"]
    if not isinstance(tasks, list):
        _die("'tasks' must be an array.")
    if not tasks:
        _die("'tasks' must contain at least one task.")

    required_fields = ["id", "type", "prompt", "cwd"]
    required_fields_set = set(required_fields)
    seen_ids: set[str] = set()

    for idx, task in enumerate(tasks):
        if not isinstance(task, dict):
            _die(f"Task index {idx}: each task must be a JSON object.")

        missing = required_fields_set - set(task.keys())
        if missing:
            _die(f"Task index {idx}: missing required fields {sorted(missing)}")

        for field in required_fields:
            if not isinstance(task[field], str):
                _die(f"Task index {idx}: field '{field}' must be a string.")

        tid = task["id"]
        try:
            _validate_path_component(tid, f"Task index {idx} id")
        except ValueError as exc:
            _die(str(exc))
        if tid in seen_ids:
            _die(f"Duplicate task id: '{tid}'")
        seen_ids.add(tid)

        task_type = task["type"]
        if task_type not in TYPE_CONFIG:
            print(
                f"Warning: unknown task type '{task_type}' for task '{tid}'; using default config.",
                file=sys.stderr,
            )

    # Warn if multiple workspace-write tasks share the same cwd.
    ws_write_cwds: dict[str, list[str]] = {}
    for task in tasks:
        cfg = TYPE_CONFIG.get(task["type"], DEFAULT_CONFIG)
        if cfg["sandbox"] == "workspace-write":
            ws_write_cwds.setdefault(task["cwd"], []).append(task["id"])
    for cwd_val, ids in ws_write_cwds.items():
        if len(ids) > 1:
            print(
                f"Warning: multiple workspace-write tasks share cwd '{cwd_val}': {ids}",
                file=sys.stderr,
            )

    return tasks


# ---------------------------------------------------------------------------
# Path validation
# ---------------------------------------------------------------------------


def _resolve_task_cwd(repo_root: str, cwd: str, tid: str) -> str:
    repo_root_real = os.path.realpath(repo_root)
    if os.path.isabs(cwd):
        raise ValueError(
            f"Task {tid!r} has absolute cwd {cwd!r}; only relative paths are allowed."
        )

    resolved_cwd = os.path.realpath(os.path.join(repo_root_real, cwd))
    if os.path.commonpath([repo_root_real, resolved_cwd]) != repo_root_real:
        raise ValueError(
            f"Task {tid!r} cwd {cwd!r} resolves outside repo root {repo_root_real!r}."
        )
    return resolved_cwd


def _prepare_tasks(tasks: list[dict[str, Any]], repo_root: str) -> list[dict[str, Any]]:
    prepared: list[dict[str, Any]] = []
    for task in tasks:
        prepared_task = dict(task)
        prepared_task["resolved_cwd"] = _resolve_task_cwd(
            repo_root, task["cwd"], task["id"]
        )
        prepared.append(prepared_task)
    return prepared


# ---------------------------------------------------------------------------
# Stream helpers
# ---------------------------------------------------------------------------


def _stream_pipe(
    source: Any,
    destination: Any,
    *,
    summary_limit: int | None = None,
) -> tuple[int, bytes]:
    total_bytes = 0
    summary_chunks: list[bytes] = []
    remaining_summary = summary_limit

    while True:
        chunk = source.read(4096)
        if not chunk:
            break

        destination.write(chunk)
        total_bytes += len(chunk)

        if remaining_summary is not None and remaining_summary > 0:
            summary_chunk = chunk[:remaining_summary]
            summary_chunks.append(summary_chunk)
            remaining_summary -= len(summary_chunk)

    destination.flush()
    return total_bytes, b"".join(summary_chunks)


# ---------------------------------------------------------------------------
# Single-task runner (executed inside a thread)
# ---------------------------------------------------------------------------


def run_task(
    task: dict[str, Any],
    artifact_dir: str,
    model: str | None,
) -> dict[str, Any]:
    """Run one Codex subagent task. Returns a result dict for the summary."""

    tid = task["id"]
    task_type = task["type"]
    prompt = task["prompt"]

    cfg = TYPE_CONFIG.get(task_type, DEFAULT_CONFIG)
    sandbox = cfg["sandbox"]
    effort = cfg["effort"]

    resolved_cwd = task["resolved_cwd"]
    task_dir = os.path.join(artifact_dir, tid)
    os.makedirs(task_dir, exist_ok=True)

    # Write prompt file.
    with open(os.path.join(task_dir, "prompt.txt"), "w", encoding="utf-8") as f:
        f.write(prompt)

    prompt_path = os.path.join(task_dir, "prompt.txt")
    # Build command (never shell=True).
    cmd: list[str] = [
        "codex", "e", "-",
        "-s", sandbox,
        "-c", f'model_reasoning_effort="{effort}"',
        "-C", resolved_cwd,
    ]
    if model:
        cmd.extend(["-m", model])

    # Snapshot git state before launch for workspace-write tasks.
    pre_files: list[str] | None = None
    if sandbox == "workspace-write":
        pre_files = _git_changed_files(resolved_cwd)

    t0 = time.monotonic()
    pid_path = os.path.join(task_dir, "pid")
    stdout_path = os.path.join(task_dir, "stdout.txt")
    stderr_path = os.path.join(task_dir, "stderr.txt")
    stdout_thread_result: dict[str, tuple[int, bytes]] = {}
    thread_errors: list[Exception] = []
    runner_error: Exception | None = None
    elapsed = 0.0
    stdout_size = 0
    stdout_summary_bytes = b""
    files_changed: list[str] | None = None
    proc: subprocess.Popen[bytes] | None = None

    try:
        with open(prompt_path, "rb") as prompt_file:
            proc = subprocess.Popen(
                cmd,
                stdin=prompt_file,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )

        with open(pid_path, "w", encoding="utf-8") as f:
            f.write(str(proc.pid))

        with open(stdout_path, "wb") as stdout_file, open(stderr_path, "wb") as stderr_file:
            def _read_stdout() -> None:
                try:
                    stdout_thread_result["value"] = _stream_pipe(
                        proc.stdout,
                        stdout_file,
                        summary_limit=MAX_OUTPUT_BYTES,
                    )
                except Exception as exc:  # noqa: BLE001
                    thread_errors.append(exc)

            def _read_stderr() -> None:
                try:
                    _stream_pipe(proc.stderr, stderr_file)
                except Exception as exc:  # noqa: BLE001
                    thread_errors.append(exc)

            stdout_thread = threading.Thread(target=_read_stdout)
            stderr_thread = threading.Thread(target=_read_stderr)
            stdout_thread.start()
            stderr_thread.start()
            while True:
                try:
                    proc.wait(timeout=0.5)
                    break
                except subprocess.TimeoutExpired:
                    if thread_errors:
                        try:
                            proc.kill()
                        except Exception:  # noqa: BLE001
                            pass
                        break
            proc.wait()
            stdout_thread.join()
            stderr_thread.join()

        elapsed = time.monotonic() - t0
        if thread_errors:
            runner_error = thread_errors[0]
        else:
            stdout_size, stdout_summary_bytes = stdout_thread_result["value"]
    except Exception as exc:  # noqa: BLE001
        elapsed = time.monotonic() - t0
        runner_error = exc
        if proc is not None and proc.poll() is None:
            proc.kill()
            proc.wait()
    finally:
        if sandbox == "workspace-write" and pre_files is not None:
            post_files = _git_changed_files(resolved_cwd)
            files_changed = sorted(set(post_files) - set(pre_files))

        meta: dict[str, Any] = {
            "exit_code": proc.returncode if proc is not None else -1,
            "elapsed_seconds": round(elapsed, 3),
            "sandbox": sandbox,
            "effort": effort,
            "model": model if model else None,
            "files_changed": files_changed,
        }
        if runner_error is not None:
            meta["runner_error"] = repr(runner_error)
        with open(os.path.join(task_dir, "meta.json"), "w", encoding="utf-8") as f:
            json.dump(meta, f, indent=2)

        try:
            os.remove(pid_path)
        except OSError:
            pass

    if runner_error is not None:
        raise runner_error

    # Build summary entry.
    truncated = stdout_size > MAX_OUTPUT_BYTES
    output_for_summary = stdout_summary_bytes.decode("utf-8", errors="ignore")

    return {
        "id": tid,
        "type": task_type,
        "status": "success" if proc.returncode == 0 else "failure",
        "exit_code": proc.returncode,
        "elapsed_seconds": round(elapsed, 3),
        "output": output_for_summary,
        "truncated": truncated,
        "files_changed": files_changed,
    }


def _build_failure_result(
    task: dict[str, Any],
    artifact_dir: str,
    exc: Exception,
) -> dict[str, Any]:
    meta = _read_task_meta(artifact_dir, task["id"])
    return {
        "id": task["id"],
        "type": task.get("type", "unknown"),
        "status": "failure",
        "exit_code": meta.get("exit_code", -1) if meta else -1,
        "elapsed_seconds": meta.get("elapsed_seconds", 0) if meta else 0,
        "output": "",
        "truncated": False,
        "files_changed": meta.get("files_changed") if meta else None,
        "error": str(exc),
    }


# ---------------------------------------------------------------------------
# Main orchestrator
# ---------------------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Parallel dispatch runner for Codex CLI subagents.",
    )
    parser.add_argument("--manifest", required=True, help="Path to JSON manifest file.")
    parser.add_argument("--run-id", required=True, help="Unique run identifier.")
    parser.add_argument("--model", default=None, help="Model to pass as -m to codex e.")
    parser.add_argument(
        "--max-concurrency",
        type=int,
        default=5,
        help="Max parallel tasks (default: 5).",
    )
    args = parser.parse_args()

    if args.max_concurrency < 1:
        _die("--max-concurrency must be at least 1.")

    try:
        run_id = _validate_path_component(args.run_id, "run_id")
    except ValueError as exc:
        _die(str(exc))

    # Pre-flight.
    preflight()

    # Load & validate manifest.
    tasks = load_manifest(args.manifest)

    # Resolve repo root.
    repo_root = _get_repo_root(args.manifest)
    try:
        tasks = _prepare_tasks(tasks, repo_root)
    except ValueError as exc:
        _die(str(exc))

    # Create artifact directory.
    artifact_dir = os.path.join(repo_root, ".context", "codex-subagent", run_id)
    os.makedirs(artifact_dir, exist_ok=True)

    # Dispatch tasks in parallel.
    results: list[dict[str, Any]] = []
    overall_t0 = time.monotonic()
    max_workers = max(1, min(len(tasks), args.max_concurrency))

    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        futures = {
            pool.submit(run_task, task, artifact_dir, args.model): task
            for task in tasks
        }
        for future in as_completed(futures):
            task = futures[future]
            try:
                results.append(future.result())
            except Exception as exc:  # noqa: BLE001
                results.append(_build_failure_result(task, artifact_dir, exc))

    total_elapsed = time.monotonic() - overall_t0

    # Sort results by original task order.
    id_order = {t["id"]: i for i, t in enumerate(tasks)}
    results.sort(key=lambda r: id_order.get(r["id"], 0))

    succeeded = sum(1 for r in results if r["status"] == "success")
    failed = sum(1 for r in results if r["status"] == "failure")

    summary = {
        "run_id": args.run_id,
        "total_elapsed_seconds": round(total_elapsed, 3),
        "total_tasks": len(tasks),
        "succeeded": succeeded,
        "failed": failed,
        "tasks": results,
    }

    # Write summary artifact.
    summary_path = os.path.join(artifact_dir, "summary.json")
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    # Print summary to stdout.
    print(json.dumps(summary, indent=2))

    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
