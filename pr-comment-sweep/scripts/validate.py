#!/usr/bin/env python3
"""Run pr-comment-sweep helper self-tests."""

from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[2]
for script in ("fetch_feedback.py", "push_head.py", "resolve_threads.py"):
    result = subprocess.run(
        (sys.executable, f"pr-comment-sweep/scripts/{script}", "--self-test"),
        cwd=ROOT,
    )
    if result.returncode:
        raise SystemExit(result.returncode)
