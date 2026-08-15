#!/usr/bin/env python3
"""Emit complete PR feedback JSON through bundled helper."""

import os
from pathlib import Path
import sys


if len(sys.argv) > 2:
    raise SystemExit("usage: fetch-pr-feedback.py [PR]")
args = ["node", str(Path(__file__).resolve().with_name("pr-feedback.mjs")), "fetch"]
if len(sys.argv) == 2:
    args.extend(("--pr", sys.argv[1]))
args.append("--json")
os.execvp("node", args)
