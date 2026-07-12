#!/usr/bin/env python3
"""Run issue-workbench's public checks."""

from pathlib import Path
import os
import subprocess
import sys
import tempfile


ROOT = Path(__file__).resolve().parents[2]
RUNTIME = tuple((ROOT / "issue-workbench/scripts" / name) for name in ("repository.py", "issue_snapshot.py", "branch_name.py"))
source = "\n".join(path.read_text() for path in RUNTIME)
for forbidden in ("def issue(", 'run(["gh",', "json.loads(run(command))"):
    if forbidden in source:
        raise SystemExit(f"issue-workbench owns github-adapter responsibility: {forbidden}")
for required in ("from github_adapter import", "GITHUB.issue_json", "GITHUB.default_branch", "GITHUB.authenticate"):
    if required not in source:
        raise SystemExit(f"issue-workbench does not route through github-adapter: {required}")
with tempfile.TemporaryDirectory() as directory:
    result = subprocess.run(
        (sys.executable, str(ROOT / "issue-workbench/scripts/issue_snapshot.py"), "--help"),
        text=True,
        capture_output=True,
        env={**os.environ, "SKILLS_ROOT": directory},
    )
    if result.returncode == 0 or "github-adapter not found" not in result.stderr:
        raise SystemExit("issue-workbench missing-adapter fixture did not fail clearly")
CHECKS = (
    ("issue-workbench/scripts/issue_snapshot.py", "--self-test"),
    ("issue-workbench/scripts/branch_name.py", "123", "Add Thing!!"),
    ("issue-workbench/scripts/start_issue_branch.py", "--self-test"),
    ("issue-workbench/scripts/integration_child.py", "--self-test"),
    ("issue-workbench/scripts/diff_guard.py", "--self-test"),
)


for check in CHECKS:
    result = subprocess.run((sys.executable, *check), cwd=ROOT)
    if result.returncode:
        raise SystemExit(result.returncode)
