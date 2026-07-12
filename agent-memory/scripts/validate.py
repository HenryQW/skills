#!/usr/bin/env python3
"""Run agent-memory's public checks."""

from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[2]
CHECKS = (
    ("agent-memory/scripts/trusted_write.py", "--self-test"),
    ("agent-memory/scripts/setup_agent_memory.py", "--self-test"),
    ("agent-memory/scripts/memory_context.py", "--self-test"),
    ("agent-memory/scripts/append_decision.py", "--self-test"),
    ("agent-memory/scripts/distill_memory.py", "--self-test"),
)


for check in CHECKS:
    result = subprocess.run((sys.executable, *check), cwd=ROOT)
    if result.returncode:
        raise SystemExit(result.returncode)
