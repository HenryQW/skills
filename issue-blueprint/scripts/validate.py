#!/usr/bin/env python3
"""Run issue-blueprint's public checks."""

from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[2]
for check in ("issue_graph_contract.py", "render_issue_plan.py", "publish_issue_plan.py"):
    result = subprocess.run((sys.executable, f"issue-blueprint/scripts/{check}", "--self-test"), cwd=ROOT)
    if result.returncode:
        raise SystemExit(result.returncode)
