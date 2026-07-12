#!/usr/bin/env python3
"""Run shipyard's public checks."""

from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[2]
for check in ("manifest.py", "inspect_parent_issue.py"):
    result = subprocess.run((sys.executable, f"shipyard/scripts/{check}", "--self-test"), cwd=ROOT)
    if result.returncode:
        raise SystemExit(result.returncode)
