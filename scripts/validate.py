#!/usr/bin/env python3
"""Run the repository's lightweight validation checks."""

from __future__ import annotations

import subprocess
import sys


CHECKS = (
    ("issue blueprint render", ["python3", "issue-blueprint/scripts/render_issue_plan.py", "--self-test"]),
    ("issue blueprint publish", ["python3", "issue-blueprint/scripts/publish_issue_plan.py", "--self-test"]),
    ("review repairbay comments", ["python3", "review-repairbay/scripts/fetch_comments.py", "--self-test"]),
    ("issue branch name", ["python3", "issue-workbench/scripts/branch_name.py", "123", "Add Thing!!"]),
    ("issue branch start", ["python3", "issue-workbench/scripts/start_issue_branch.py", "--self-test"]),
    ("issue integration child", ["python3", "issue-workbench/scripts/integration_child.py", "--self-test"]),
    ("diff guard", ["python3", "issue-workbench/scripts/diff_guard.py"]),
    ("ci repairbay help", ["python3", "ci-repairbay/scripts/inspect_pr_checks.py", "--help"]),
    ("shipyard parent inspection", ["python3", "shipyard/scripts/inspect_parent_issue.py", "--self-test"]),
    ("agent memory setup", ["python3", "agent-memory/scripts/setup_agent_memory.py", "--self-test"]),
)


def main() -> int:
    for name, command in CHECKS:
        result = subprocess.run(command, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        if result.returncode != 0:
            print(f"{name} failed:", file=sys.stderr)
            print(result.stdout, file=sys.stderr)
            return result.returncode
    print(f"validate ok: {len(CHECKS)} checks")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
