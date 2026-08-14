#!/usr/bin/env python3
"""Merge fetched origin/main into current non-main worktree branch."""

from __future__ import annotations

import argparse
import contextlib
import io
import os
import subprocess
import sys
import tempfile
from pathlib import Path

REMOTE_MAIN_SOURCE = "refs/heads/main"
REMOTE_MAIN_REF = "refs/remotes/origin/main"
LOCAL_MAIN_REF = "refs/heads/main"
IN_PROGRESS_PATHS = (
    "MERGE_HEAD",
    "CHERRY_PICK_HEAD",
    "REVERT_HEAD",
    "rebase-apply",
    "rebase-merge",
    "sequencer",
)


class MergeError(RuntimeError):
    pass


def run(args: list[str], *, cwd: Path | None = None, check: bool = True) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        ["git", *args],
        cwd=cwd,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if check and result.returncode:
        detail = (result.stderr or result.stdout).strip()
        raise MergeError(detail or f"git {' '.join(args)} failed")
    return result


def git(args: list[str], *, cwd: Path | None = None) -> str:
    return run(args, cwd=cwd).stdout.strip()


def revision(ref: str) -> str:
    return git(["rev-parse", "--verify", f"{ref}^{{commit}}"])


def optional_revision(ref: str) -> str | None:
    result = run(["rev-parse", "--verify", "--quiet", f"{ref}^{{commit}}"], check=False)
    if result.returncode == 0:
        return result.stdout.strip()
    if result.returncode == 1:
        return None
    detail = (result.stderr or result.stdout).strip()
    raise MergeError(detail or f"could not resolve {ref}")


def current_branch_ref() -> str:
    result = run(["symbolic-ref", "--quiet", "HEAD"], check=False)
    if result.returncode:
        raise MergeError("HEAD must name a local branch")
    ref = result.stdout.strip()
    if ref == LOCAL_MAIN_REF:
        raise MergeError("refusing to merge main into main")
    if not ref.startswith("refs/heads/"):
        raise MergeError(f"HEAD must name refs/heads/*, got {ref}")
    return ref


def has_git_path(name: str) -> bool:
    return Path(git(["rev-parse", "--git-path", name])).exists()


def active_operation() -> str | None:
    return next((name for name in IN_PROGRESS_PATHS if has_git_path(name)), None)


def unmerged_paths() -> list[str]:
    return git(["diff", "--name-only", "--diff-filter=U"]).splitlines()


def status_lines() -> list[str]:
    return git(["status", "--porcelain=v1", "--untracked-files=all"]).splitlines()


def require_ready_worktree() -> str:
    if git(["rev-parse", "--is-inside-work-tree"]) != "true":
        raise MergeError("current directory must be inside a worktree")
    operation = active_operation()
    if operation:
        raise MergeError(f"Git operation already active: {operation}")
    if unmerged_paths():
        raise MergeError("worktree has unresolved conflicts")
    return current_branch_ref()


def stash_dirty_worktree() -> str | None:
    if not status_lines():
        return None
    before = optional_revision("refs/stash")
    run(["stash", "push", "--include-untracked", "--message", "merge-main"])
    stash_oid = revision("refs/stash")
    if stash_oid == before:
        raise MergeError("git stash did not create a backup")
    if status_lines():
        raise MergeError(f"stash {stash_oid} did not clean worktree")
    return stash_oid


def fetch_main() -> str:
    run(["fetch", "--no-tags", "origin", f"+{REMOTE_MAIN_SOURCE}:{REMOTE_MAIN_REF}"])
    return revision(REMOTE_MAIN_REF)


def is_ancestor(ancestor: str, descendant: str) -> bool:
    result = run(["merge-base", "--is-ancestor", ancestor, descendant], check=False)
    if result.returncode == 0:
        return True
    if result.returncode == 1:
        return False
    detail = (result.stderr or result.stdout).strip()
    raise MergeError(detail or "git merge-base failed")


def restore_stash(stash_oid: str) -> tuple[bool, str, str]:
    if optional_revision("refs/stash") == stash_oid:
        result = run(["stash", "pop", "--index", "stash@{0}"], check=False)
        state = "popped"
    else:
        result = run(["stash", "apply", "--index", stash_oid], check=False)
        state = "retained"
    detail = (result.stderr or result.stdout).strip().replace("\n", " | ")
    return result.returncode == 0, state, detail


def emit(
    status: str,
    branch_ref: str,
    head_before: str,
    main_sha: str,
    stash_oid: str | None,
    stash_state: str,
) -> None:
    fields = (
        ("status", status),
        ("branch_ref", branch_ref),
        ("head_before", head_before),
        ("main_ref", REMOTE_MAIN_REF),
        ("main_sha", main_sha),
        ("head_after", revision("HEAD")),
        ("stash_oid", stash_oid or "none"),
        ("stash_state", stash_state),
    )
    print(" ".join(f"{key}={value}" for key, value in fields))


def merge_main() -> int:
    branch_ref = require_ready_worktree()
    head_before = revision("HEAD")
    stash_oid: str | None = None
    main_sha = "none"
    try:
        stash_oid = stash_dirty_worktree()
        main_sha = fetch_main()
        if current_branch_ref() != branch_ref or revision(branch_ref) != head_before:
            raise MergeError("current branch moved before merge")
        if is_ancestor(main_sha, "HEAD"):
            outcome = "up_to_date"
        else:
            result = run(["merge", "--ff", "--no-edit", main_sha], check=False)
            if result.returncode:
                detail = (result.stderr or result.stdout).strip().replace("\n", " | ")
                if unmerged_paths():
                    emit("merge_conflict", branch_ref, head_before, main_sha, stash_oid, "retained")
                    print(f"error: {detail}", file=sys.stderr)
                    return 2
                raise MergeError(detail or "git merge failed")
            outcome = "merged"

        if stash_oid:
            restored, stash_state, detail = restore_stash(stash_oid)
            if not restored:
                status = "stash_conflict" if unmerged_paths() else "stash_restore_failed"
                emit(status, branch_ref, head_before, main_sha, stash_oid, "retained")
                print(f"error: {detail}", file=sys.stderr)
                return 3
        else:
            stash_state = "none"
        emit(outcome, branch_ref, head_before, main_sha, stash_oid, stash_state)
        return 0
    except MergeError as error:
        if stash_oid and not active_operation():
            restored, stash_state, detail = restore_stash(stash_oid)
            if not restored:
                error = MergeError(f"{error}; stash backup retained at {stash_oid}: {detail}")
            elif stash_state == "retained":
                error = MergeError(f"{error}; stash restored but retained at {stash_oid}")
        elif stash_oid:
            error = MergeError(f"{error}; stash backup retained at {stash_oid}")
        print(f"error: {error}", file=sys.stderr)
        return 1


def test_git(path: Path, *args: str) -> str:
    return git(list(args), cwd=path)


def setup_repo(root: Path) -> tuple[Path, Path]:
    root.mkdir()
    origin = root / "origin.git"
    seed = root / "seed"
    repo = root / "repo"
    run(["init", "--bare", os.fspath(origin)])
    run(["init", os.fspath(seed)])
    test_git(seed, "checkout", "-b", "main")
    test_git(seed, "config", "user.email", "agent@example.invalid")
    test_git(seed, "config", "user.name", "Agent")
    (seed / "shared.txt").write_text("base\n", encoding="utf-8")
    (seed / "conflict.txt").write_text("base\n", encoding="utf-8")
    test_git(seed, "add", ".")
    test_git(seed, "commit", "-m", "init")
    test_git(seed, "remote", "add", "origin", os.fspath(origin))
    test_git(seed, "push", "-u", "origin", "main")
    run(["--git-dir", os.fspath(origin), "symbolic-ref", "HEAD", LOCAL_MAIN_REF])
    run(["clone", os.fspath(origin), os.fspath(repo)])
    test_git(repo, "config", "user.email", "agent@example.invalid")
    test_git(repo, "config", "user.name", "Agent")
    test_git(repo, "checkout", "-b", "feature")
    return seed, repo


def commit(path: Path, name: str, value: str, message: str) -> str:
    (path / name).write_text(value, encoding="utf-8")
    test_git(path, "add", name)
    test_git(path, "commit", "-m", message)
    return test_git(path, "rev-parse", "HEAD")


def merge_in(path: Path) -> tuple[int, str]:
    previous = Path.cwd()
    output = io.StringIO()
    try:
        os.chdir(path)
        with contextlib.redirect_stdout(output), contextlib.redirect_stderr(io.StringIO()):
            return merge_main(), output.getvalue()
    finally:
        os.chdir(previous)


def self_test() -> None:
    with tempfile.TemporaryDirectory() as raw_tmp:
        root = Path(raw_tmp)
        seed, repo = setup_repo(root / "clean")
        commit(repo, "feature.txt", "feature\n", "test: feature")
        main_sha = commit(seed, "main.txt", "main\n", "test: main")
        test_git(seed, "push", "origin", "main")
        (repo / "staged.txt").write_text("staged\n", encoding="utf-8")
        test_git(repo, "add", "staged.txt")
        (repo / "untracked.txt").write_text("untracked\n", encoding="utf-8")
        result, output = merge_in(repo)
        assert result == 0
        assert f"main_ref={REMOTE_MAIN_REF}" in output
        assert f"main_sha={main_sha}" in output
        assert "stash_state=popped" in output
        assert test_git(repo, "rev-parse", REMOTE_MAIN_REF) == main_sha
        assert (repo / "main.txt").read_text(encoding="utf-8") == "main\n"
        assert "A  staged.txt" in test_git(repo, "status", "--porcelain=v1", "--untracked-files=all")
        assert (repo / "untracked.txt").read_text(encoding="utf-8") == "untracked\n"
        assert not test_git(repo, "stash", "list")

        seed, repo = setup_repo(root / "conflict")
        commit(repo, "conflict.txt", "feature\n", "test: feature")
        main_sha = commit(seed, "conflict.txt", "main\n", "test: main")
        test_git(seed, "push", "origin", "main")
        (repo / "deferred.txt").write_text("deferred\n", encoding="utf-8")
        result, output = merge_in(repo)
        assert result == 2
        stash_oid = test_git(repo, "rev-parse", "refs/stash")
        assert "status=merge_conflict" in output
        assert f"main_sha={main_sha}" in output
        assert f"stash_oid={stash_oid}" in output
        assert not (repo / "deferred.txt").exists()
        assert test_git(repo, "diff", "--name-only", "--diff-filter=U") == "conflict.txt"
        assert test_git(repo, "rev-parse", REMOTE_MAIN_REF) == main_sha
        test_git(repo, "merge", "--abort")
        test_git(repo, "stash", "apply", "--index", stash_oid)
        assert (repo / "deferred.txt").read_text(encoding="utf-8") == "deferred\n"


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true", help="Run internal checks and exit")
    args = parser.parse_args(argv)
    if args.self_test:
        self_test()
        print("merge-main self-test ok: dirty restore and conflict backup")
        return 0
    return merge_main()


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
