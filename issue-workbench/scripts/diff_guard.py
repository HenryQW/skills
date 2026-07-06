#!/usr/bin/env python3
"""Fail when repository changes include paths this skill must not touch."""

from __future__ import annotations

import argparse
import fnmatch
import os
import subprocess
import sys
import tempfile
from pathlib import Path


FORBIDDEN_PATTERNS = (
    ".context/*",
    ".agents/*",
    ".env",
    ".env.*",
    "*.pem",
    "*.key",
    "*secret*",
    "*credential*",
    "package-lock.json",
    "pnpm-lock.yaml",
    "yarn.lock",
    "poetry.lock",
    "Pipfile.lock",
    "uv.lock",
    "Cargo.lock",
    "Gemfile.lock",
    "composer.lock",
    "dist/*",
    "build/*",
    "coverage/*",
    "generated/*",
    "__generated__/*",
    ".github/workflows/*",
    "Dockerfile",
    "docker-compose*.yml",
    "docker-compose*.yaml",
    "infra/*",
    "ops/*",
    "deploy/*",
    "k8s/*",
    "helm/*",
    "*.tf",
)


def git(args: list[str]) -> list[str]:
    result = subprocess.run(["git", *args], check=True, text=True, stdout=subprocess.PIPE)
    return [line for line in result.stdout.splitlines() if line]


def working_tree_files() -> tuple[set[str], set[str], set[str]]:
    staged_files = set(git(["diff", "--cached", "--name-only"]))
    files = set(git(["diff", "--name-only"])) | staged_files
    untracked: set[str] = set()
    for line in git(["status", "--short", "--untracked-files=all"]):
        path = line[3:] if line.startswith("?? ") else line[3:].strip()
        if " -> " in path:
            path = path.rsplit(" -> ", 1)[1]
        if path:
            files.add(path)
            if line.startswith("?? "):
                untracked.add(path)
    return files, untracked, staged_files


def changed_files(base: str | None) -> tuple[list[str], set[str], set[str], set[str]]:
    files, untracked, staged_files = working_tree_files()
    branch_files: set[str] = set()
    if base:
        branch_files = set(git(["diff", "--name-only", f"{base}...HEAD"]))
        files.update(branch_files)
    return sorted(files), untracked, branch_files, staged_files


def is_forbidden(path: str, allowed: set[str]) -> bool:
    normalized = path.replace("\\", "/")
    if normalized in allowed or any(normalized.startswith(f"{item.rstrip('/')}/") for item in allowed):
        return False
    return any(fnmatch.fnmatch(normalized, pattern) for pattern in FORBIDDEN_PATTERNS)


def is_untracked_context_scratch(
    path: str,
    untracked: set[str],
    branch_files: set[str],
    staged_files: set[str],
) -> bool:
    normalized = path.replace("\\", "/")
    return (
        normalized in untracked
        and normalized not in branch_files
        and normalized not in staged_files
        and normalized.startswith(".context/")
    )


def self_test() -> None:
    with tempfile.TemporaryDirectory() as raw_tmp:
        old_cwd = os.getcwd()
        try:
            os.chdir(raw_tmp)
            subprocess.run(["git", "init"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            Path(".context").mkdir()
            Path(".context/progress.md").write_text("scratch\n", encoding="utf-8")
            Path(".context/review.diff").write_text("diff\n", encoding="utf-8")
            files, untracked, branch_files, staged_files = changed_files(None)
            blocked = [
                path
                for path in files
                if not is_untracked_context_scratch(path, untracked, branch_files, staged_files)
                and is_forbidden(path, set())
            ]
            assert ".context/progress.md" in untracked
            assert ".context/review.diff" in untracked
            assert blocked == []
            Path(".env").write_text("secret\n", encoding="utf-8")
            files, untracked, branch_files, staged_files = changed_files(None)
            blocked = [
                path
                for path in files
                if not is_untracked_context_scratch(path, untracked, branch_files, staged_files)
                and is_forbidden(path, set())
            ]
            assert ".env" in blocked

            Path(".env").unlink()
            Path(".context/progress.md").unlink()
            Path(".context/review.diff").unlink()
            subprocess.run(["git", "config", "user.email", "agent@example.invalid"], check=True)
            subprocess.run(["git", "config", "user.name", "Agent"], check=True)
            Path("README.md").write_text("base\n", encoding="utf-8")
            subprocess.run(["git", "add", "README.md"], check=True)
            subprocess.run(["git", "commit", "-m", "base"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            base = git(["rev-parse", "HEAD"])[0]
            Path(".context/progress.md").write_text("tracked scratch\n", encoding="utf-8")
            subprocess.run(["git", "add", ".context/progress.md"], check=True)
            subprocess.run(["git", "commit", "-m", "add context"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            subprocess.run(["git", "rm", "--cached", ".context/progress.md"], check=True, stdout=subprocess.PIPE)
            files, untracked, branch_files, staged_files = changed_files(None)
            blocked = [
                path
                for path in files
                if not is_untracked_context_scratch(path, untracked, branch_files, staged_files)
                and is_forbidden(path, set())
            ]
            assert ".context/progress.md" in untracked
            assert ".context/progress.md" in staged_files
            assert ".context/progress.md" in blocked
            files, untracked, branch_files, staged_files = changed_files(base)
            blocked = [
                path
                for path in files
                if not is_untracked_context_scratch(path, untracked, branch_files, staged_files)
                and is_forbidden(path, set())
            ]
            assert ".context/progress.md" in branch_files
            assert ".context/progress.md" in blocked
        finally:
            os.chdir(old_cwd)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Check changed paths against skill forbidden paths. Includes unstaged, staged, branch, and untracked paths."
    )
    parser.add_argument("--base", help="Check branch diff against this base branch")
    parser.add_argument("--allow", action="append", default=[], help="Explicitly allowed path or directory")
    parser.add_argument("--self-test", action="store_true", help="Run internal checks and exit")
    args = parser.parse_args()

    if args.self_test:
        self_test()
        return 0

    try:
        files, untracked, branch_files, staged_files = changed_files(args.base)
    except subprocess.CalledProcessError as exc:
        print(exc, file=sys.stderr)
        return exc.returncode

    blocked = [
        path
        for path in files
        if not is_untracked_context_scratch(path, untracked, branch_files, staged_files)
        and is_forbidden(path, set(args.allow))
    ]
    if blocked:
        print("Forbidden changed paths:", file=sys.stderr)
        for path in blocked:
            print(f"- {path}", file=sys.stderr)
        if untracked:
            print("Note: untracked files are included; use git add -N when you need them in git diff --stat.", file=sys.stderr)
        return 1

    note = "; untracked included, use git add -N to show new-file content in git diff --stat" if untracked else ""
    print(f"diff_guard ok: {len(files)} changed path{'s' if len(files) != 1 else ''}{note}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
