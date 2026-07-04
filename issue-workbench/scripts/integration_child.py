#!/usr/bin/env python3
"""Glue for issue-workbench integration-mode children."""

from __future__ import annotations

import argparse
import os
import sys
import tempfile
from pathlib import Path

from start_issue_branch import create_issue_branch
from start_issue_branch import run


def emit(lines: list[str]) -> None:
    for line in lines:
        print(line)


def start_child(issue_number: str, worktree_path: str, integration_branch: str, branch_slug: str | None) -> list[str]:
    return [
        *create_issue_branch(
            issue_number,
            branch_slug=branch_slug,
            worktree_path=worktree_path,
            integration_branch=integration_branch,
        ),
        f"review_base={integration_branch}",
    ]


def changed_code_status() -> list[str]:
    lines = run(["git", "status", "--short"]).splitlines()
    return [line for line in lines if not line[3:].startswith(".context/")]


def finish_child(review_base: str, verification: str) -> list[str]:
    if not (verification.startswith("pass:") or verification.startswith("skip:")):
        raise RuntimeError("--verification must start with pass: or skip:")
    dirty = changed_code_status()
    if dirty:
        raise RuntimeError("uncommitted non-context changes remain:\n" + "\n".join(dirty))
    diff_stat = run(["git", "diff", "--stat", f"{review_base}...HEAD"]).replace("\n", " | ")
    return [
        f"branch={run(['git', 'branch', '--show-current'])}",
        f"worktree={Path.cwd()}",
        f"commit={run(['git', 'rev-parse', 'HEAD'])}",
        f"diff_stat={diff_stat}",
        f"verification={verification}",
    ]


def merge_child(branch: str, integration_branch: str) -> None:
    current = run(["git", "branch", "--show-current"])
    if current != integration_branch:
        raise RuntimeError(f"expected integration branch {integration_branch}, got {current}")
    dirty = changed_code_status()
    if dirty:
        raise RuntimeError("uncommitted non-context changes remain:\n" + "\n".join(dirty))
    run(["git", "merge", "--no-ff", "--no-edit", branch])


def assert_raises(message: str, func, *args) -> None:
    try:
        func(*args)
    except RuntimeError as exc:
        assert message in str(exc)
    else:
        raise AssertionError(f"expected RuntimeError containing {message!r}")


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
        run(["git", "config", "user.email", "agent@example.invalid"], cwd=os.fspath(repo))
        run(["git", "config", "user.name", "Agent"], cwd=os.fspath(repo))

        old_cwd = os.getcwd()
        try:
            os.chdir(repo)
            run(["git", "checkout", "-B", "integration", "origin/main"])
            assert start_child("123", os.fspath(worktree), "integration", None) == [
                "branch=issue-123",
                f"worktree={worktree}",
                "review_base=integration",
            ]
            os.chdir(worktree)
            Path("README.md").write_text("seed\nchild\n", encoding="utf-8")
            run(["git", "add", "README.md"])
            run(["git", "commit", "-m", "fix(test): child change"])
            assert_raises("pass:", finish_child, "integration", "maybe")
            Path("dirty.txt").write_text("dirty\n", encoding="utf-8")
            assert_raises("uncommitted non-context", finish_child, "integration", "pass:demo")
            Path("dirty.txt").unlink()
            finish = finish_child("integration", "pass:demo")
            assert finish[0] == "branch=issue-123"
            assert Path(finish[1].split("=", 1)[1]).resolve() == worktree.resolve()
            assert finish[3].startswith("diff_stat=")
            assert_raises("expected integration branch", merge_child, "issue-123", "integration")
            os.chdir(repo)
            Path("dirty.txt").write_text("dirty\n", encoding="utf-8")
            assert_raises("uncommitted non-context", merge_child, "issue-123", "integration")
            Path("dirty.txt").unlink()
            merge_child("issue-123", "integration")
            assert "child" in Path("README.md").read_text(encoding="utf-8")
        finally:
            os.chdir(old_cwd)
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Manage issue-workbench integration child glue.")
    parser.add_argument("--self-test", action="store_true")
    subparsers = parser.add_subparsers(dest="command")

    start = subparsers.add_parser("start")
    start.add_argument("issue_number")
    start.add_argument("--worktree-path", required=True)
    start.add_argument("--integration-branch", required=True)
    start.add_argument("--branch-slug")

    finish = subparsers.add_parser("finish")
    finish.add_argument("--review-base", required=True)
    finish.add_argument("--verification", required=True)

    merge = subparsers.add_parser("merge")
    merge.add_argument("branch")
    merge.add_argument("--integration-branch", required=True)

    args = parser.parse_args()

    try:
        if args.self_test:
            return self_test()
        if args.command == "start":
            emit(start_child(args.issue_number, args.worktree_path, args.integration_branch, args.branch_slug))
        elif args.command == "finish":
            emit(finish_child(args.review_base, args.verification))
        elif args.command == "merge":
            merge_child(args.branch, args.integration_branch)
        else:
            parser.error("command is required unless --self-test is used")
        return 0
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
