#!/usr/bin/env python3
"""Fail when repository changes include paths this skill must not touch."""

from __future__ import annotations

import argparse
import fnmatch
import subprocess
import sys


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


def working_tree_files() -> set[str]:
    files = set(git(["diff", "--name-only"]) + git(["diff", "--cached", "--name-only"]))
    for line in git(["status", "--short"]):
        path = line[3:] if line.startswith("?? ") else line[3:].strip()
        if " -> " in path:
            path = path.rsplit(" -> ", 1)[1]
        if path:
            files.add(path)
    return files


def changed_files(base: str | None) -> list[str]:
    files = working_tree_files()
    if base:
        files.update(git(["diff", "--name-only", f"{base}...HEAD"]))
    return sorted(files)


def is_forbidden(path: str, allowed: set[str]) -> bool:
    normalized = path.replace("\\", "/")
    if normalized in allowed or any(normalized.startswith(f"{item.rstrip('/')}/") for item in allowed):
        return False
    return any(fnmatch.fnmatch(normalized, pattern) for pattern in FORBIDDEN_PATTERNS)


def main() -> int:
    parser = argparse.ArgumentParser(description="Check changed paths against skill forbidden paths.")
    parser.add_argument("--base", help="Check branch diff against this base branch")
    parser.add_argument("--allow", action="append", default=[], help="Explicitly allowed path or directory")
    args = parser.parse_args()

    try:
        files = changed_files(args.base)
    except subprocess.CalledProcessError as exc:
        print(exc, file=sys.stderr)
        return exc.returncode

    blocked = [path for path in files if is_forbidden(path, set(args.allow))]
    if blocked:
        print("Forbidden changed paths:", file=sys.stderr)
        for path in blocked:
            print(f"- {path}", file=sys.stderr)
        return 1

    print(f"diff_guard ok: {len(files)} changed path{'s' if len(files) != 1 else ''}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
