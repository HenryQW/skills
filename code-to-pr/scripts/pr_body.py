#!/usr/bin/env python3
"""Draft a concise PR body from git diff and commit state."""

from __future__ import annotations

import argparse
import subprocess
import sys


def git(args: list[str]) -> str:
    result = subprocess.run(
        ["git", *args],
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return result.stdout.strip()


def commit_subjects(base_branch: str) -> list[str]:
    output = git(["log", "--format=%s", f"{base_branch}..HEAD"])
    return [line for line in output.splitlines() if line][:4]


def changed_files(base_branch: str) -> list[str]:
    output = git(["diff", "--name-only", f"{base_branch}...HEAD"])
    return [line for line in output.splitlines() if line]


def main() -> int:
    parser = argparse.ArgumentParser(description="Draft a PR body for code-to-pr.")
    parser.add_argument("base_branch", help="Base branch used for the PR diff")
    parser.add_argument("--issue-number", help="GitHub issue number")
    parser.add_argument(
        "--issue-link",
        choices=("closes", "refs"),
        default="refs",
        help="How to link the issue when --issue-number is provided",
    )
    parser.add_argument(
        "--test",
        action="append",
        dest="tests",
        help="Testing command or result; repeat for multiple entries",
    )
    args = parser.parse_args()

    try:
        subjects = commit_subjects(args.base_branch)
        files = changed_files(args.base_branch)
    except subprocess.CalledProcessError as exc:
        print(exc.stderr.strip() or str(exc), file=sys.stderr)
        return exc.returncode

    summary = subjects or [f"Update {len(files)} file{'s' if len(files) != 1 else ''}"]
    tests = args.tests or ["Not run"]
    scope = [
        f"Diff scope: `git diff {args.base_branch}...HEAD`",
        f"Changed files: {len(files)}",
    ]

    print("## Summary")
    for item in summary[:4]:
        print(f"- {item}")

    print("\n## Testing")
    for item in tests:
        print(f"- {item}")

    print("\n## Scope")
    for item in scope:
        print(f"- {item}")

    if args.issue_number:
        verb = "Closes" if args.issue_link == "closes" else "Refs"
        print(f"\n{verb} #{args.issue_number}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
