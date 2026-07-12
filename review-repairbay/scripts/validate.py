#!/usr/bin/env python3
"""Run review-repairbay's public checks."""

from pathlib import Path
import os
import subprocess
import sys
import tempfile


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "review-repairbay/scripts/fetch_comments.py"
source = SCRIPT.read_text()
for forbidden in ("def _run(", "def _run_json", "def parse_pr_url", "def resolve_pr_ref", '["gh",'):
    if forbidden in source:
        raise SystemExit(f"review-repairbay owns github-adapter responsibility: {forbidden}")
for required in ("from github_adapter import", "GITHUB.graphql", "GITHUB.resolve_pr"):
    if required not in source:
        raise SystemExit(f"review-repairbay does not route through github-adapter: {required}")
with tempfile.TemporaryDirectory() as directory:
    result = subprocess.run(
        (sys.executable, str(SCRIPT), "--help"),
        text=True,
        capture_output=True,
        env={**os.environ, "SKILLS_ROOT": directory},
    )
    if result.returncode == 0 or "github-adapter not found" not in result.stderr:
        raise SystemExit("review-repairbay missing-adapter fixture did not fail clearly")
raise SystemExit(
    subprocess.run((sys.executable, str(SCRIPT), "--self-test"), cwd=ROOT).returncode
)
