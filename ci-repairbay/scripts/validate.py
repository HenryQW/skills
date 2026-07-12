#!/usr/bin/env python3
"""Run ci-repairbay's public checks."""

from pathlib import Path
import os
import subprocess
import sys
import tempfile


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "ci-repairbay/scripts/inspect_pr_checks.py"
source = SCRIPT.read_text()
for forbidden in ("def run_gh_command", "def run_gh_command_raw", "def fetch_repo_slug", '["gh",'):
    if forbidden in source:
        raise SystemExit(f"ci-repairbay owns github-adapter responsibility: {forbidden}")
for required in ("from github_adapter import", "GITHUB.execute", "GITHUB.resolve_pr"):
    if required not in source:
        raise SystemExit(f"ci-repairbay does not route through github-adapter: {required}")
with tempfile.TemporaryDirectory() as directory:
    result = subprocess.run(
        (sys.executable, str(SCRIPT), "--help"),
        text=True,
        capture_output=True,
        env={**os.environ, "SKILLS_ROOT": directory},
    )
    if result.returncode == 0 or "github-adapter not found" not in result.stderr:
        raise SystemExit("ci-repairbay missing-adapter fixture did not fail clearly")
raise SystemExit(subprocess.run((sys.executable, str(SCRIPT), "--self-test"), cwd=ROOT).returncode)
