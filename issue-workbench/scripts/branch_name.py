#!/usr/bin/env python3
"""Print the deterministic branch name for issue-workbench."""

from __future__ import annotations

import argparse
import sys

from repository import (
    CommandError,
    GITHUB,
    GitHubError,
    branch_name,
    integration_branch_name,
    integration_branch_name_from_title,
    normalize_slug,
)


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
        GITHUB.authenticate()
        print(integration_branch_name(args.parent_issue, args.repo))
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    except CommandError as exc:
        print(str(exc), file=sys.stderr)
        return exc.returncode
    except GitHubError as exc:
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
