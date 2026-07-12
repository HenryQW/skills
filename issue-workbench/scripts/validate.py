#!/usr/bin/env python3
"""Run issue-workbench's public checks."""

from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[2]
CHECKS = (
    ("issue-workbench/scripts/issue_snapshot.py", "--self-test"),
    ("issue-workbench/scripts/branch_name.py", "123", "Add Thing!!"),
    ("issue-workbench/scripts/start_issue_branch.py", "--self-test"),
    ("issue-workbench/scripts/integration_child.py", "--self-test"),
    ("issue-workbench/scripts/diff_guard.py",),
)


for check in CHECKS:
    result = subprocess.run((sys.executable, *check), cwd=ROOT)
    if result.returncode:
        raise SystemExit(result.returncode)
