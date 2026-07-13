#!/usr/bin/env python3
"""Run ci-repairbay's public checks."""

from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[2]
raise SystemExit(subprocess.run((sys.executable, "ci-repairbay/scripts/inspect_pr_checks.py", "--self-test"), cwd=ROOT).returncode)
