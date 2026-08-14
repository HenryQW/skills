#!/usr/bin/env python3
"""Emit complete PR feedback JSON through shared helper."""

import os
import sys


if len(sys.argv) != 2:
    raise SystemExit("usage: fetch-pr-feedback.py PR")
os.execvp(
    "node",
    ["node", "scripts/pr-feedback.mjs", "fetch", "--pr", sys.argv[1], "--json"],
)
