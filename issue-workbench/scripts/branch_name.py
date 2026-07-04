#!/usr/bin/env python3
"""Print the deterministic branch name for issue-workbench."""

from __future__ import annotations

import argparse
import re
import sys


def normalize_slug(raw: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", raw.lower()).strip("-")
    slug = re.sub(r"-{2,}", "-", slug)
    return slug


def branch_name(issue_number: str, branch_slug: str | None = None) -> str:
    if not re.fullmatch(r"[1-9][0-9]*", issue_number):
        raise ValueError("issue_number must be a positive integer")

    if not branch_slug:
        return f"issue-{issue_number}"

    slug = normalize_slug(branch_slug)
    if not slug:
        raise ValueError("branch_slug must contain at least one letter or digit")

    return f"issue-{issue_number}-{slug}"


def main() -> int:
    parser = argparse.ArgumentParser(description="Print an issue branch name.")
    parser.add_argument("issue_number", help="GitHub issue number")
    parser.add_argument("branch_slug", nargs="?", help="Optional branch slug")
    args = parser.parse_args()

    try:
        print(branch_name(args.issue_number, args.branch_slug))
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
