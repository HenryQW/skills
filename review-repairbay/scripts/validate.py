#!/usr/bin/env python3
"""Run review-repairbay's public checks."""

from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[2]
raise SystemExit(
    subprocess.run((sys.executable, "review-repairbay/scripts/fetch_comments.py", "--self-test"), cwd=ROOT).returncode
)
