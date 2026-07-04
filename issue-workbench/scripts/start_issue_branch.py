#!/usr/bin/env python3
"""Create the issue-workbench branch in the current repo or a worktree."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
import tempfile
from pathlib import Path

from branch_name import branch_name


def run(command: list[str], *, cwd: str | None = None) -> str:
    result = subprocess.run(command, cwd=cwd, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip()
        raise RuntimeError(detail or f"{command[0]} exited {result.returncode}")
    return result.stdout.strip()


def ref_exists(ref: str) -> bool:
    return subprocess.run(["git", "show-ref", "--verify", "--quiet", ref]).returncode == 0


def remote_branch_exists(name: str) -> bool:
    result = subprocess.run(
        ["git", "ls-remote", "--heads", "origin", name],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip()
        raise RuntimeError(detail or "git ls-remote failed")
    return bool(result.stdout.strip())


def default_branch() -> str:
    return run(["gh", "repo", "view", "--json", "defaultBranchRef", "--jq", ".defaultBranchRef.name"])


def create_issue_branch(
    issue_number: str,
    *,
    base_branch: str | None = None,
    branch_slug: str | None = None,
    worktree_path: str | None = None,
    integration_branch: str | None = None,
) -> list[str]:
    name = branch_name(issue_number, branch_slug)
    if ref_exists(f"refs/heads/{name}"):
        raise RuntimeError(f"local branch already exists: {name}")
    if remote_branch_exists(name):
        raise RuntimeError(f"origin branch already exists: {name}")

    run(["git", "fetch", "origin"])

    if worktree_path:
        if not integration_branch:
            raise RuntimeError("--integration-branch is required with --worktree-path")
        path = Path(worktree_path)
        if path.exists():
            raise RuntimeError(f"worktree path already exists: {path}")
        run(["git", "worktree", "add", "-b", name, os.fspath(path), integration_branch])
        return [f"branch={name}", f"worktree={path}"]

    if integration_branch:
        raise RuntimeError("--integration-branch requires --worktree-path")

    base = base_branch or default_branch()
    run(["git", "checkout", "-b", name, f"origin/{base}"])
    return [f"branch={name}"]


def self_test() -> int:
    assert branch_name("123") == "issue-123"
    assert branch_name("123", "Add Thing!!") == "issue-123-add-thing"
    try:
        branch_name("0")
    except ValueError:
        pass
    else:
        raise AssertionError("invalid issue number accepted")

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
            assert create_issue_branch(
                "124",
                branch_slug="Child Slice",
                worktree_path=os.fspath(worktree),
                integration_branch="integration",
            ) == [f"branch=issue-124-child-slice", f"worktree={worktree}"]
            assert run(["git", "-C", os.fspath(worktree), "branch", "--show-current"]) == "issue-124-child-slice"
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
