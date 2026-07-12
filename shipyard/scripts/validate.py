#!/usr/bin/env python3
"""Run shipyard's public checks."""

from pathlib import Path
import os
import subprocess
import sys
import tempfile


ROOT = Path(__file__).resolve().parents[2]
INSPECT = ROOT / "shipyard/scripts/inspect_parent_issue.py"
source = INSPECT.read_text()
for forbidden in ("def gh_json", "def repo_view_args", "def issue_number", '["gh",'):
    if forbidden in source:
        raise SystemExit(f"shipyard owns github-adapter responsibility: {forbidden}")
for required in ("from github_adapter import", "GITHUB.issue_json", "GITHUB.resolve_issue", "GITHUB.default_branch"):
    if required not in source:
        raise SystemExit(f"shipyard does not route through github-adapter: {required}")
with tempfile.TemporaryDirectory() as directory:
    (Path(directory) / "issue-blueprint/scripts").mkdir(parents=True)
    result = subprocess.run(
        (sys.executable, str(INSPECT), "--help"),
        text=True,
        capture_output=True,
        env={**os.environ, "SKILLS_ROOT": directory},
    )
    if result.returncode == 0 or "github-adapter not found" not in result.stderr:
        raise SystemExit("shipyard missing-adapter fixture did not fail clearly")
for check in ("manifest.py", "inspect_parent_issue.py"):
    result = subprocess.run((sys.executable, f"shipyard/scripts/{check}", "--self-test"), cwd=ROOT)
    if result.returncode:
        raise SystemExit(result.returncode)
