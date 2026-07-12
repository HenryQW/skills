#!/usr/bin/env python3
"""Run github-adapter's public checks."""

from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[2]
raise SystemExit(
    subprocess.run((sys.executable, "github-adapter/scripts/github_adapter.py", "--self-test"), cwd=ROOT).returncode
)
