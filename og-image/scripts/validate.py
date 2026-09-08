#!/usr/bin/env python3
"""Run the OG renderer self-test."""

from pathlib import Path
import subprocess


SCRIPT = Path(__file__).with_name("render-og.mjs")
raise SystemExit(subprocess.run(("node", str(SCRIPT), "--self-test")).returncode)
