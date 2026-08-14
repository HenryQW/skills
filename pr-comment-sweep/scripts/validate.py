#!/usr/bin/env python3
"""Run PR feedback helper regression checks."""

from pathlib import Path
import subprocess


ROOT = Path(__file__).resolve().parents[2]
compile((ROOT / "scripts/fetch-pr-feedback.py").read_text(), "fetch-pr-feedback.py", "exec")
for command in (
    ("node", "scripts/pr-feedback.mjs", "self-test"),
    ("sh", "-n", "scripts/verify-pr-target.sh"),
):
    result = subprocess.run(command, cwd=ROOT)
    if result.returncode:
        raise SystemExit(result.returncode)
