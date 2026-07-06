#!/usr/bin/env python3
"""Glue for issue-workbench integration-mode children."""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import sys
import tempfile
from pathlib import Path

from start_issue_branch import create_issue_branch
from start_issue_branch import run


def emit(lines: list[str]) -> None:
    for line in lines:
        print(line)


def emit_json(value: dict[str, object]) -> None:
    print(json.dumps(value, sort_keys=True))


def repo_requires_progress(root: Path) -> bool:
    instructions = root / "AGENTS.md"
    return instructions.exists() and ".context/progress.md" in instructions.read_text(encoding="utf-8")


def ensure_progress_file(source_root: Path, child_root: Path) -> None:
    if not repo_requires_progress(source_root):
        return
    target = child_root / ".context" / "progress.md"
    target.parent.mkdir(parents=True, exist_ok=True)
    source = source_root / ".context" / "progress.md"
    if source.exists():
        shutil.copyfile(source, target)
    else:
        target.write_text("# Progress\n\n- [ ] Continue issue-workbench integration child.\n", encoding="utf-8")


def start_child(issue_number: str, worktree_path: str, integration_branch: str, branch_slug: str | None) -> list[str]:
    source_root = Path.cwd()
    lines = [
        *create_issue_branch(
            issue_number,
            branch_slug=branch_slug,
            worktree_path=worktree_path,
            integration_branch=integration_branch,
        ),
        f"review_base={integration_branch}",
    ]
    ensure_progress_file(source_root, Path(worktree_path))
    return lines


def changed_code_status() -> list[str]:
    lines = run(["git", "status", "--short"]).splitlines()
    return [line for line in lines if not line[3:].startswith(".context/")]


def ensure_local_progress_file() -> Path:
    progress = Path.cwd() / ".context" / "progress.md"
    progress.parent.mkdir(parents=True, exist_ok=True)
    if not progress.exists():
        progress.write_text("# Progress\n", encoding="utf-8")
    return progress


def append_handoff_record(progress: Path, result: dict[str, object]) -> None:
    record = {
        "branch": result["branch"],
        "base": result["base"],
        "commit": result["commit"],
        "verification": result["verification"],
        "review": result["review"],
        "checks": result["checks"],
        "known_skips": result["known_skips"],
    }
    if "needs_child_fix" in result:
        record["needs_child_fix"] = result["needs_child_fix"]
    with progress.open("a", encoding="utf-8") as f:
        f.write("\n## Integration Handoff\n\n")
        f.write("```json\n")
        f.write(json.dumps(record, sort_keys=True))
        f.write("\n```\n")


def finish_child(
    review_base: str,
    verification: str,
    review: str,
    checks: list[str] | None = None,
    known_skips: list[str] | None = None,
    needs_child_fix: str | None = None,
) -> dict[str, object]:
    if not (verification.startswith("pass:") or verification.startswith("skip:")):
        raise RuntimeError("--verification must start with pass: or skip:")
    if review not in {"PASS", "FAIL"}:
        raise RuntimeError("--review must be PASS or FAIL")
    if review == "FAIL" and not needs_child_fix:
        raise RuntimeError("--review FAIL requires --needs-child-fix #123")
    if needs_child_fix and not re.fullmatch(r"#[1-9][0-9]*", needs_child_fix):
        raise RuntimeError("--needs-child-fix must look like #123")
    dirty = changed_code_status()
    if dirty:
        raise RuntimeError("uncommitted non-context changes remain:\n" + "\n".join(dirty))
    run(["git", "merge-base", "--is-ancestor", review_base, "HEAD"])
    progress = ensure_local_progress_file()
    result: dict[str, object] = {
        "branch": run(["git", "branch", "--show-current"]),
        "worktree": os.fspath(Path.cwd()),
        "base": review_base,
        "commit": run(["git", "rev-parse", "HEAD"]),
        "diff_stat": run(["git", "diff", "--stat", f"{review_base}...HEAD"]).replace("\n", " | "),
        "verification": verification,
        "review": review,
        "checks": checks or [],
        "known_skips": known_skips or [],
        "artifacts": {"progress_path": os.fspath(progress)},
    }
    if needs_child_fix:
        result["needs_child_fix"] = needs_child_fix
    append_handoff_record(progress, result)
    return result


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
            Path("integration.txt").write_text("shipyard branch\n", encoding="utf-8")
            run(["git", "add", "integration.txt"])
            run(["git", "commit", "-m", "test: integration base"])
            integration_head = run(["git", "rev-parse", "integration"])
            assert start_child("123", os.fspath(worktree), "integration", None) == [
                "branch=issue-123",
                f"worktree={worktree}",
                "review_base=integration",
            ]
            os.chdir(worktree)
            assert run(["git", "rev-parse", "HEAD"]) == integration_head
            assert Path("integration.txt").read_text(encoding="utf-8") == "shipyard branch\n"
            Path("README.md").write_text("seed\nchild\n", encoding="utf-8")
            run(["git", "add", "README.md"])
            run(["git", "commit", "-m", "fix(test): child change"])
            assert_raises("pass:", finish_child, "integration", "maybe", "PASS")
            Path("dirty.txt").write_text("dirty\n", encoding="utf-8")
            assert_raises("uncommitted non-context", finish_child, "integration", "pass:demo", "PASS")
            Path("dirty.txt").unlink()
            assert_raises("PASS or FAIL", finish_child, "integration", "pass:demo", "MAYBE")
            assert_raises("requires --needs-child-fix", finish_child, "integration", "skip:needs child fix", "FAIL")
            assert_raises("#123", finish_child, "integration", "skip:needs child fix", "FAIL", [], [], "123")
            assert_raises("#123", finish_child, "integration", "skip:needs child fix", "FAIL", [], [], "#abc")
            assert_raises("#123", finish_child, "integration", "skip:needs child fix", "FAIL", [], [], "#123 extra")
            finish = finish_child("integration", "pass:demo", "PASS", ["python -m test"], ["slow check"])
            assert finish["branch"] == "issue-123"
            assert Path(str(finish["worktree"])).resolve() == worktree.resolve()
            assert finish["base"] == "integration"
            assert str(finish["diff_stat"])
            assert finish["review"] == "PASS"
            assert finish["checks"] == ["python -m test"]
            assert finish["known_skips"] == ["slow check"]
            progress_path = Path(str(finish["artifacts"]["progress_path"]))
            assert progress_path.resolve() == (worktree / ".context" / "progress.md").resolve()
            assert '"commit"' in progress_path.read_text(encoding="utf-8")
            fail = finish_child("integration", "skip:needs child fix", "FAIL", needs_child_fix="#123")
            assert fail["needs_child_fix"] == "#123"
            assert_raises("expected integration branch", merge_child, "issue-123", "integration")
            os.chdir(repo)
            Path("dirty.txt").write_text("dirty\n", encoding="utf-8")
            assert_raises("uncommitted non-context", merge_child, "issue-123", "integration")
            Path("dirty.txt").unlink()
            merge_child("issue-123", "integration")
            assert "child" in Path("README.md").read_text(encoding="utf-8")
            (repo / "AGENTS.md").write_text("Use .context/progress.md\n", encoding="utf-8")
            (repo / ".context").mkdir()
            (repo / ".context" / "progress.md").write_text("# Progress\n\nseed\n", encoding="utf-8")
            second = tmp / "child-2"
            start_child("125", os.fspath(second), "integration", None)
            assert (second / ".context" / "progress.md").read_text(encoding="utf-8") == "# Progress\n\nseed\n"
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
    finish.add_argument("--review", required=True, choices=["PASS", "FAIL"])
    finish.add_argument("--check", action="append", default=[])
    finish.add_argument("--known-skip", action="append", default=[])
    finish.add_argument("--needs-child-fix")

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
            emit_json(
                finish_child(
                    args.review_base,
                    args.verification,
                    args.review,
                    args.check,
                    args.known_skip,
                    args.needs_child_fix,
                )
            )
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
