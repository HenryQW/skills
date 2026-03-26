#!/usr/bin/env python3
"""Parallel dispatch runner for Codex CLI subagents.

Reads a JSON manifest of tasks, launches them as parallel Codex CLI
invocations, and writes structured artifacts + a summary JSON to stdout.
"""

from __future__ import annotations

import argparse
import json
import os
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

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _die(msg: str) -> None:
    print(msg, file=sys.stderr)
    sys.exit(2)


def _get_repo_root() -> str:
    result = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        _die(f"Failed to detect git repo root: {result.stderr.strip()}")
    return result.stdout.strip()


def _git_changed_files(cwd: str) -> list[str]:
    """Return list of changed file names in *cwd* via ``git diff --name-only``."""
    result = subprocess.run(
        ["git", "diff", "--name-only"],
        capture_output=True,
        text=True,
        cwd=cwd,
    )
    if result.returncode != 0:
        return []
    return [f for f in result.stdout.strip().splitlines() if f]


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
        missing = required_fields - set(task.keys())
        if missing:
            _die(f"Task index {idx}: missing required fields {sorted(missing)}")

        for field in required_fields:
            if not isinstance(task[field], str):
                _die(f"Task index {idx}: field '{field}' must be a string.")

        tid = task["id"]
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
# Single-task runner (executed inside a thread)
# ---------------------------------------------------------------------------


def run_task(
    task: dict[str, Any],
    artifact_dir: str,
    repo_root: str,
    model: str | None,
    semaphore: threading.Semaphore,
) -> dict[str, Any]:
    """Run one Codex subagent task. Returns a result dict for the summary."""

    tid = task["id"]
    task_type = task["type"]
    prompt = task["prompt"]

    cfg = TYPE_CONFIG.get(task_type, DEFAULT_CONFIG)
    sandbox = cfg["sandbox"]
    effort = cfg["effort"]

    resolved_cwd = os.path.realpath(os.path.join(repo_root, task["cwd"]))
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

    # Acquire semaphore to respect max concurrency.
    with semaphore:
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

    # Pre-flight.
    preflight()

    # Load & validate manifest.
    tasks = load_manifest(args.manifest)

    # Resolve repo root.
    repo_root = _get_repo_root()

    # Create artifact directory.
    artifact_dir = os.path.join(".context", "codex-subagent", args.run_id)
    os.makedirs(artifact_dir, exist_ok=True)

    # Dispatch tasks in parallel.
    semaphore = threading.Semaphore(args.max_concurrency)
    results: list[dict[str, Any]] = []
    overall_t0 = time.time()

    with ThreadPoolExecutor(max_workers=len(tasks) or 1) as pool:
        futures = {
            pool.submit(
                run_task, task, artifact_dir, repo_root, args.model, semaphore
            ): task["id"]
            for task in tasks
        }
        for future in as_completed(futures):
            results.append(future.result())

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
