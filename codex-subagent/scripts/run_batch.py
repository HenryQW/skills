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
    repo_probe_cwd = start_path
    if os.path.isfile(start_path):
        repo_probe_cwd = os.path.dirname(start_path)

    result = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        capture_output=True,
        text=True,
        cwd=repo_probe_cwd,
    )
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
    """Return changed and untracked file names in *cwd* via ``git status --porcelain``."""
    result = subprocess.run(
        ["git", "status", "--porcelain"],
        capture_output=True,
        text=True,
        cwd=cwd,
    )
    if result.returncode != 0:
        return []

    files: set[str] = set()
    for line in result.stdout.splitlines():
        if not line.strip():
            continue

        path_part = line[3:]
        if " -> " in path_part:
            _, path_part = path_part.split(" -> ", 1)
        if path_part:
            files.add(path_part)

    return sorted(files)


# ---------------------------------------------------------------------------
# Pre-flight checks
# ---------------------------------------------------------------------------


def preflight() -> None:
    if shutil.which("codex") is None:
        _die("Error: 'codex' not found on PATH. Install Codex CLI first.")

    result = subprocess.run(
        ["codex", "login", "status"],
        capture_output=True,
        text=True,
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

    required_fields = {"id", "type", "prompt", "cwd"}
    seen_ids: set[str] = set()

    for idx, task in enumerate(tasks):
        if not isinstance(task, dict):
            _die(f"Task index {idx}: each task must be a JSON object.")

        missing = required_fields - set(task.keys())
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

    # Build command (never shell=True).
    cmd: list[str] = [
        "codex", "e", prompt,
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

    t0 = time.time()
    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    # Write PID file.
    pid_path = os.path.join(task_dir, "pid")
    with open(pid_path, "w", encoding="utf-8") as f:
        f.write(str(proc.pid))

    stdout_bytes, stderr_bytes = proc.communicate()
    elapsed = time.time() - t0

    # Decode output.
    stdout_text = stdout_bytes.decode("utf-8", errors="replace")
    stderr_text = stderr_bytes.decode("utf-8", errors="replace")

    # Write stdout / stderr artifacts.
    with open(os.path.join(task_dir, "stdout.txt"), "w", encoding="utf-8") as f:
        f.write(stdout_text)
    with open(os.path.join(task_dir, "stderr.txt"), "w", encoding="utf-8") as f:
        f.write(stderr_text)

    # Remove PID file.
    try:
        os.remove(pid_path)
    except OSError:
        pass

    # Compute files-changed delta for workspace-write tasks.
    files_changed: list[str] | None = None
    if sandbox == "workspace-write" and pre_files is not None:
        post_files = _git_changed_files(resolved_cwd)
        files_changed = sorted(set(post_files) - set(pre_files))

    # Write meta.json.
    meta = {
        "exit_code": proc.returncode,
        "elapsed_seconds": round(elapsed, 3),
        "sandbox": sandbox,
        "effort": effort,
        "model": model if model else None,
        "files_changed": files_changed,
    }
    with open(os.path.join(task_dir, "meta.json"), "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)

    # Build summary entry.
    truncated = len(stdout_text.encode("utf-8")) > MAX_OUTPUT_BYTES
    output_for_summary = stdout_text
    if truncated:
        output_for_summary = stdout_text.encode("utf-8")[:MAX_OUTPUT_BYTES].decode(
            "utf-8", errors="ignore"
        )

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


def _build_failure_result(task: dict[str, Any], exc: Exception) -> dict[str, Any]:
    return {
        "id": task["id"],
        "type": task.get("type", "unknown"),
        "status": "failure",
        "exit_code": -1,
        "elapsed_seconds": 0,
        "output": "",
        "truncated": False,
        "files_changed": None,
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
    overall_t0 = time.time()
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
                results.append(_build_failure_result(task, exc))

    total_elapsed = time.time() - overall_t0

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
