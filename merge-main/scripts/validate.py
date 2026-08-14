#!/usr/bin/env python3
"""Run merge-main helper self-test."""

from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[2]
raise SystemExit(
    subprocess.run(
        (sys.executable, "merge-main/scripts/merge_main.py", "--self-test"), cwd=ROOT
    ).returncode
)
