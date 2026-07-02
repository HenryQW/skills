#!/usr/bin/env python3
"""Draft a concise PR body from git diff and commit state."""

from __future__ import annotations

import argparse
import subprocess
import sys
from collections import Counter
from pathlib import Path


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


def pr_templates() -> list[Path]:
    candidates = []
    for root in (Path("."), Path("docs"), Path(".github")):
        if not root.exists():
            continue
        candidates.extend(
            path
            for path in root.iterdir()
            if path.is_file() and path.stem.lower() == "pull_request_template"
        )
        directory = next(
            (path for path in root.iterdir() if path.is_dir() and path.name.lower() == "pull_request_template"),
            None,
        )
        if directory:
            candidates.extend(path for path in directory.iterdir() if path.is_file())
    return sorted(candidates)


def file_groups(files: list[str]) -> list[str]:
    counts = Counter(path.split("/", 1)[0] for path in files)
    return [f"{name}: {count}" for name, count in counts.most_common(6)]


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
    parser.add_argument("--body-file", help="Write the body to this path instead of stdout")
    parser.add_argument(
        "--ignore-template",
        action="store_true",
        help="Draft a fallback body even when a PR template exists",
    )
    args = parser.parse_args()

    templates = pr_templates()
    if templates and not args.ignore_template:
        print("PR template exists; use it instead:", file=sys.stderr)
        for template in templates:
            print(f"- {template}", file=sys.stderr)
        return 2

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
    scope.extend(f"File group: {item}" for item in file_groups(files))

    lines = ["## Summary"]
    for item in summary[:4]:
        lines.append(f"- {item}")

    lines.append("\n## Testing")
    for item in tests:
        lines.append(f"- {item}")

    lines.append("\n## Scope")
    for item in scope:
        lines.append(f"- {item}")

    if args.issue_number:
        verb = "Closes" if args.issue_link == "closes" else "Refs"
        lines.append(f"\n{verb} #{args.issue_number}")

    body = "\n".join(lines) + "\n"
    if args.body_file:
        Path(args.body_file).write_text(body)
    else:
        print(body, end="")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
