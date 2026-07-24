#!/usr/bin/env python3
"""Glue for issue-workbench integration-mode children."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import tempfile
from pathlib import Path

from repository import create_issue_branch, current_branch, diff_snapshot, revision, run, status_lines

SHIPYARD_SCRIPTS = Path(__file__).resolve().parents[2] / "shipyard" / "scripts"
sys.path.insert(0, os.fspath(SHIPYARD_SCRIPTS))
from manifest import write_child_handoff  # noqa: E402


def emit(lines: list[str]) -> None:
    for line in lines:
        print(line)


HANDOFF_NAME = "integration-handoff.json"


def repo_requires_progress(root: Path) -> bool:
    instructions = root / "AGENTS.md"
    return instructions.exists() and ".context/progress.md" in instructions.read_text(encoding="utf-8")


def progress_state(
    goal: str,
    current_step: str,
    artifacts: dict[str, object] | None = None,
    blockers: list[object] | None = None,
    validation: list[str] | None = None,
) -> dict[str, object]:
    return {
        "goal": goal,
        "current_step": current_step,
        "artifacts": artifacts or {},
        "blockers": blockers or [],
        "validation": validation or [],
    }


def write_progress(
    progress: Path,
    goal: str,
    current_step: str,
    artifacts: dict[str, object] | None = None,
    blockers: list[object] | None = None,
    validation: list[str] | None = None,
) -> None:
    progress.parent.mkdir(parents=True, exist_ok=True)
    progress.write_text(json.dumps(progress_state(goal, current_step, artifacts, blockers, validation), indent=2) + "\n", encoding="utf-8")


def ensure_progress_file(source_root: Path, child_root: Path, issue_number: str) -> None:
    if not repo_requires_progress(source_root):
        return
    target = child_root / ".context" / "progress.md"
    source = source_root / ".context" / "progress.md"
    artifacts: dict[str, object] = {}
    if source.exists():
        artifacts["source_progress"] = os.fspath(source.resolve())
    write_progress(target, f"issue-workbench #{issue_number}", "implement integration child", artifacts)


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
    ensure_progress_file(source_root, Path(worktree_path), issue_number)
    return lines


def changed_code_status() -> list[str]:
    return [line for line in status_lines() if not line[3:].startswith(".context/")]


def ensure_local_progress_file() -> Path:
    progress = Path.cwd() / ".context" / "progress.md"
    if not progress.exists():
        write_progress(progress, "issue-workbench integration child", "finish handoff")
    return progress


def record_handoff_progress(
    progress: Path,
    handoff: Path,
    review: str,
    needs_child_fix: str | None,
) -> Path:
    blockers = []
    if needs_child_fix:
        blockers.append({"needs_child_fix": needs_child_fix})
    artifacts: dict[str, object] = {"handoff": os.fspath(handoff.resolve())}
    if review == "PENDING_REVIEW":
        current = json.loads(progress.read_text(encoding="utf-8"))
        artifacts["pending_review"] = current["artifacts"]["pending_review"]
    write_progress(
        progress,
        "issue-workbench integration child",
        "handoff ready",
        artifacts,
        blockers,
    )
    return handoff.resolve()


def write_handoff(
    progress: Path,
    review_base: str,
    review: str,
    checks: list[str],
    known_skips: list[str],
    needs_child_fix: str | None,
    branch: str,
    issue: str,
    head_sha: str,
    changed_files: list[str],
    diff_stat: str,
) -> Path:
    handoff = progress.parent / HANDOFF_NAME
    facts = {
        "issue": issue,
        "branch": branch,
        "worktree": os.fspath(Path.cwd()),
        "base_ref": review_base,
        "base_sha": revision(review_base),
        "head_sha": head_sha,
        "changed_files": changed_files,
        "diff_stat": diff_stat,
        "review": review,
        "checks": checks,
        "known_skips": known_skips,
        "needs_child_fix": needs_child_fix,
    }
    if review == "PENDING_REVIEW":
        facts["progress_path"] = os.fspath(progress)
    try:
        write_child_handoff(handoff, facts)
    except SystemExit as exc:
        raise RuntimeError(str(exc)) from None
    return record_handoff_progress(progress, handoff, review, needs_child_fix)


def finish_child(
    review_base: str,
    review: str,
    checks: list[str] | None = None,
    known_skips: list[str] | None = None,
    needs_child_fix: str | None = None,
) -> Path:
    dirty = changed_code_status()
    if dirty:
        raise RuntimeError("uncommitted non-context changes remain:\n" + "\n".join(dirty))
    run(["git", "merge-base", "--is-ancestor", review_base, "HEAD"])
    progress = ensure_local_progress_file()
    branch = current_branch()
    match = re.fullmatch(r"issue-([1-9][0-9]*)(?:-[a-z0-9][a-z0-9-]*)?", branch)
    if not match:
        raise RuntimeError("integration child branch must look like issue-123 or issue-123-slug")
    head_sha = revision("HEAD")
    changed_files, diff_stat = diff_snapshot(review_base)
    return write_handoff(
        progress,
        review_base,
        review,
        checks or [],
        known_skips or [],
        needs_child_fix,
        branch,
        f"#{match.group(1)}",
        head_sha,
        changed_files,
        diff_stat,
    )


def merge_child(branch: str, integration_branch: str, expected_head: str | None = None) -> None:
    current = current_branch()
    if current != integration_branch:
        raise RuntimeError(f"expected integration branch {integration_branch}, got {current}")
    dirty = changed_code_status()
    if dirty:
        raise RuntimeError("uncommitted non-context changes remain:\n" + "\n".join(dirty))
    if expected_head:
        actual_head = revision(branch)
        if actual_head != expected_head:
            raise RuntimeError(f"expected {branch} at {expected_head}, got {actual_head}")
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
            assert start_child("123", os.fspath(worktree), "integration", "Child Slice") == [
                "branch=issue-123-child-slice",
                f"worktree={worktree}",
                "review_base=integration",
            ]
            os.chdir(worktree)
            assert run(["git", "rev-parse", "HEAD"]) == integration_head
            assert Path("integration.txt").read_text(encoding="utf-8") == "shipyard branch\n"
            Path("README.md").write_text("seed\nchild\n", encoding="utf-8")
            run(["git", "add", "README.md"])
            run(["git", "commit", "-m", "fix(test): child change"])
            Path("dirty.txt").write_text("dirty\n", encoding="utf-8")
            assert_raises("uncommitted non-context", finish_child, "integration", "PASS")
            Path("dirty.txt").unlink()
            assert_raises("PASS, PENDING_REVIEW, or FAIL", finish_child, "integration", "MAYBE")
            assert_raises("requires needs_child_fix", finish_child, "integration", "FAIL")
            assert_raises("#123", finish_child, "integration", "FAIL", [], [], "123")
            assert_raises("#123", finish_child, "integration", "FAIL", [], [], "#abc")
            assert_raises("#123", finish_child, "integration", "FAIL", [], [], "#123 extra")
            finish_path = finish_child("integration", "PASS", ["python -m test"], ["slow check"])
            assert finish_path == (worktree / ".context" / HANDOFF_NAME).resolve()
            finish = json.loads(finish_path.read_text(encoding="utf-8"))
            assert finish_path.read_bytes() == (json.dumps(finish, indent=2, sort_keys=True) + "\n").encode()
            assert finish["branch"] == "issue-123-child-slice"
            assert Path(str(finish["worktree"])).resolve() == worktree.resolve()
            assert finish["issue"] == "#123"
            assert finish["base_ref"] == "integration"
            assert finish["base_sha"] == integration_head
            assert finish["head_sha"] == run(["git", "rev-parse", "HEAD"])
            assert "commit" not in finish
            assert "verification" not in finish
            assert "artifacts" not in finish
            assert finish["changed_files"] == ["README.md"]
            assert str(finish["diff_stat"])
            assert finish["review"] == "PASS"
            assert finish["checks"] == ["python -m test"]
            assert finish["known_skips"] == ["slow check"]
            progress_path = worktree / ".context" / "progress.md"
            progress_data = json.loads(progress_path.read_text(encoding="utf-8"))
            assert set(progress_data) == {"goal", "current_step", "artifacts", "blockers", "validation"}
            assert progress_data["artifacts"]["handoff"] == os.fspath(finish_path)
            assert progress_data["validation"] == []
            fail_path = finish_child("integration", "FAIL", needs_child_fix="#123")
            fail = json.loads(fail_path.read_text(encoding="utf-8"))
            assert fail["needs_child_fix"] == "#123"
            write_progress(
                progress_path,
                "issue-workbench integration child",
                "review pending",
                {
                    "pending_review": {
                        "review_id": "review-1",
                        "branch": finish["branch"],
                        "local_head_sha": finish["head_sha"],
                        "upstream_sha": finish["head_sha"],
                        "base_ref": finish["base_ref"],
                        "base_sha": finish["base_sha"],
                        "poll_after_utc": "2026-01-01T00:00:00Z",
                        "progress_path": os.fspath(progress_path),
                    }
                },
            )
            pending_path = finish_child("integration", "PENDING_REVIEW")
            pending = json.loads(pending_path.read_text(encoding="utf-8"))
            assert pending["review"] == "PENDING_REVIEW"
            assert pending["pending_review"]["review_id"] == "review-1"
            pending_progress = json.loads(progress_path.read_text(encoding="utf-8"))
            assert pending_progress["artifacts"]["pending_review"] == pending["pending_review"]
            assert_raises("expected integration branch", merge_child, "issue-123-child-slice", "integration")
            os.chdir(repo)
            Path("dirty.txt").write_text("dirty\n", encoding="utf-8")
            assert_raises("uncommitted non-context", merge_child, "issue-123", "integration")
            Path("dirty.txt").unlink()
            assert_raises("expected issue-123-child-slice", merge_child, "issue-123-child-slice", "integration", "0" * 40)
            merge_child("issue-123-child-slice", "integration", str(finish["head_sha"]))
            assert "child" in Path("README.md").read_text(encoding="utf-8")
            (repo / "AGENTS.md").write_text("Use .context/progress.md\n", encoding="utf-8")
            (repo / ".context").mkdir()
            write_progress(repo / ".context" / "progress.md", "shipyard #1", "launch child")
            second = tmp / "child-2"
            start_child("125", os.fspath(second), "integration", None)
            second_data = json.loads((second / ".context" / "progress.md").read_text(encoding="utf-8"))
            assert set(second_data) == {"goal", "current_step", "artifacts", "blockers", "validation"}
            assert second_data["artifacts"]["source_progress"] == os.fspath((repo / ".context" / "progress.md").resolve())
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
    finish.add_argument("--review", required=True)
    finish.add_argument("--check", action="append", default=[])
    finish.add_argument("--known-skip", action="append", default=[])
    finish.add_argument("--needs-child-fix")

    merge = subparsers.add_parser("merge")
    merge.add_argument("branch")
    merge.add_argument("--integration-branch", required=True)
    merge.add_argument("--expected-head")

    args = parser.parse_args()

    try:
        if args.self_test:
            return self_test()
        if args.command == "start":
            emit(start_child(args.issue_number, args.worktree_path, args.integration_branch, args.branch_slug))
        elif args.command == "finish":
            print(
                finish_child(
                    args.review_base,
                    args.review,
                    args.check,
                    args.known_skip,
                    args.needs_child_fix,
                )
            )
        elif args.command == "merge":
            merge_child(args.branch, args.integration_branch, args.expected_head)
        else:
            parser.error("command is required unless --self-test is used")
        return 0
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
