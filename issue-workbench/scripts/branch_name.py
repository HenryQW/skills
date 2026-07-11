#!/usr/bin/env python3
"""Print the deterministic branch name for issue-workbench."""

from __future__ import annotations

import argparse
import re
import sys

from repository import CommandError, issue


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


def integration_branch_name_from_title(title: str) -> str:
    slug = normalize_slug(title)
    if not slug:
        raise ValueError("parent issue title must contain at least one letter or digit")
    return f"feat/{slug}"


def integration_branch_name(parent_issue: str, repo: str | None = None) -> str:
    if not re.fullmatch(r"[1-9][0-9]*", parent_issue):
        raise ValueError("parent_issue must be a positive integer")
    title = issue(parent_issue, "title", repo).get("title", "")
    return integration_branch_name_from_title(str(title))


def self_test() -> int:
    assert normalize_slug("V4 deterministic skill replacement MCP") == "v4-deterministic-skill-replacement-mcp"
    assert branch_name("123") == "issue-123"
    assert branch_name("123", "Add Thing!!") == "issue-123-add-thing"
    assert integration_branch_name_from_title("V4 deterministic skill replacement MCP") == (
        "feat/v4-deterministic-skill-replacement-mcp"
    )
    for call in (lambda: branch_name("0"), lambda: branch_name("123", "!!!"), lambda: integration_branch_name_from_title("!!!")):
        try:
            call()
        except ValueError:
            pass
        else:
            raise AssertionError("invalid input accepted")
    return 0


def legacy_main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Print an issue branch name.")
    parser.add_argument("issue_number", help="GitHub issue number")
    parser.add_argument("branch_slug", nargs="?", help="Optional branch slug")
    args = parser.parse_args(argv)

    try:
        print(branch_name(args.issue_number, args.branch_slug))
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    return 0


def integration_main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Print a shipyard integration branch name.")
    parser.add_argument("parent_issue", help="GitHub parent issue number")
    parser.add_argument("--repo", help="OWNER/REPO for gh issue lookup")
    args = parser.parse_args(argv)

    try:
        print(integration_branch_name(args.parent_issue, args.repo))
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    except CommandError as exc:
        print(str(exc), file=sys.stderr)
        return exc.returncode
    return 0


def main() -> int:
    argv = sys.argv[1:]
    if argv == ["--self-test"]:
        return self_test()
    if argv[:1] == ["integration"]:
        return integration_main(argv[1:])
    return legacy_main(argv)


if __name__ == "__main__":
    raise SystemExit(main())
