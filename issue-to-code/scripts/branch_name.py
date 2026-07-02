#!/usr/bin/env python3
"""Print the deterministic branch name for issue-to-code."""

from __future__ import annotations

import argparse
import re
import sys


def normalize_slug(raw: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", raw.lower()).strip("-")
    slug = re.sub(r"-{2,}", "-", slug)
    return slug


def main() -> int:
    parser = argparse.ArgumentParser(description="Print an issue branch name.")
    parser.add_argument("issue_number", help="GitHub issue number")
    parser.add_argument("branch_slug", nargs="?", help="Optional branch slug")
    args = parser.parse_args()

    if not re.fullmatch(r"[1-9][0-9]*", args.issue_number):
        print("issue_number must be a positive integer", file=sys.stderr)
        return 2

    if not args.branch_slug:
        print(f"issue-{args.issue_number}")
        return 0

    slug = normalize_slug(args.branch_slug)
    if not slug:
        print("branch_slug must contain at least one letter or digit", file=sys.stderr)
        return 2

    print(f"issue-{args.issue_number}-{slug}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
