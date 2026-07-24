#!/usr/bin/env python3
"""Create the issue-workbench branch in the current repo or a worktree."""

from __future__ import annotations

import argparse
import os
import sys
import tempfile
from pathlib import Path

from repository import create_issue_branch, run


def self_test() -> int:
    with tempfile.TemporaryDirectory() as raw_tmp:
        tmp = Path(raw_tmp)
        origin = tmp / "origin.git"
        seed = tmp / "seed"
        repo = tmp / "repo"
        worktree = tmp / "child"

        run(["git", "init", "--bare", os.fspath(origin)])
        run(["git", "init", os.fspath(seed)])
        run(["git", "checkout", "-b", "main"], cwd=os.fspath(seed))
        run(["git", "config", "user.email", "agent@example.invalid"], cwd=os.fspath(seed))
        run(["git", "config", "user.name", "Agent"], cwd=os.fspath(seed))
        (seed / "README.md").write_text("seed\n", encoding="utf-8")
        run(["git", "add", "README.md"], cwd=os.fspath(seed))
        run(["git", "commit", "-m", "init"], cwd=os.fspath(seed))
        run(["git", "remote", "add", "origin", os.fspath(origin)], cwd=os.fspath(seed))
        run(["git", "push", "-u", "origin", "main"], cwd=os.fspath(seed))
        run(["git", "--git-dir", os.fspath(origin), "symbolic-ref", "HEAD", "refs/heads/main"])
        run(["git", "clone", os.fspath(origin), os.fspath(repo)])

        old_cwd = os.getcwd()
        try:
            os.chdir(repo)
            assert create_issue_branch("123", base_branch="main") == ["branch=issue-123"]
            assert run(["git", "branch", "--show-current"]) == "issue-123"
            run(["git", "checkout", "-B", "integration", "origin/main"])
            Path("integration.txt").write_text("shipyard branch\n", encoding="utf-8")
            run(["git", "add", "integration.txt"])
            run(["git", "commit", "-m", "test: integration base"])
            integration_head = run(["git", "rev-parse", "integration"])
            remote_head = run(["git", "rev-parse", "origin/main"])
            run(
                [
                    "git",
                    "--git-dir",
                    os.fspath(origin),
                    "update-ref",
                    "refs/heads/issue-124-child-slice",
                    remote_head,
                ]
            )
            assert create_issue_branch(
                "124",
                branch_slug="Child Slice",
                worktree_path=os.fspath(worktree),
                integration_branch="integration",
            ) == ["branch=issue-124-child-slice", f"worktree={worktree}"]
            assert run(["git", "-C", os.fspath(worktree), "branch", "--show-current"]) == "issue-124-child-slice"
            assert run(["git", "-C", os.fspath(worktree), "rev-parse", "HEAD"]) == integration_head
            assert (worktree / "integration.txt").read_text(encoding="utf-8") == "shipyard branch\n"
            run(["git", "--git-dir", os.fspath(origin), "update-ref", "refs/heads/issue-125", remote_head])
            try:
                create_issue_branch("125", base_branch="main")
            except RuntimeError as exc:
                assert "origin branch already exists" in str(exc)
            else:
                raise AssertionError("standalone branch must reject an existing origin branch")
        finally:
            os.chdir(old_cwd)

    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Create an issue-workbench branch.")
    parser.add_argument("issue_number", nargs="?", help="GitHub issue number")
    parser.add_argument("--base-branch", help="Base branch for normal PR mode")
    parser.add_argument("--branch-slug", help="Optional branch slug")
    parser.add_argument("--worktree-path", help="Create the issue branch in this worktree")
    parser.add_argument("--integration-branch", help="Local branch used as the worktree base")
    parser.add_argument("--self-test", action="store_true", help="Run internal checks and exit")
    args = parser.parse_args()

    if args.self_test:
        return self_test()

    if not args.issue_number:
        parser.error("issue_number is required unless --self-test is set")

    try:
        for line in create_issue_branch(
            args.issue_number,
            base_branch=args.base_branch,
            branch_slug=args.branch_slug,
            worktree_path=args.worktree_path,
            integration_branch=args.integration_branch,
        ):
            print(line)
        return 0
    except (RuntimeError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
