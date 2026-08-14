#!/usr/bin/env python3
"""Run PR feedback helper regression check."""

from pathlib import Path
import subprocess


ROOT = Path(__file__).resolve().parents[2]
raise SystemExit(
    subprocess.run(("node", "scripts/pr-feedback.mjs", "self-test"), cwd=ROOT).returncode
)
