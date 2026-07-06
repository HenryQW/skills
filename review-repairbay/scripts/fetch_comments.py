#!/usr/bin/env python3
"""
Fetch all PR conversation comments + reviews + review threads (inline threads)
by shelling out to:

  gh api graphql

Requires:
  - `gh auth login` already set up

Usage:
  python fetch_comments.py --repo OWNER/REPO --pr 123 > pr_comments.json
  python fetch_comments.py --pr https://github.com/OWNER/REPO/pull/123 > pr_comments.json
  python fetch_comments.py > pr_comments.json  # current branch PR
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
from typing import Any

QUERY = """\
query(
  $owner: String!,
  $repo: String!,
  $number: Int!,
  $commentsCursor: String,
  $reviewsCursor: String,
  $threadsCursor: String
) {
  repository(owner: $owner, name: $repo) {
    pullRequest(number: $number) {
      number
      url
      title
      state

      # Top-level "Conversation" comments (issue comments on the PR)
      comments(first: 100, after: $commentsCursor) {
        pageInfo { hasNextPage endCursor }
        nodes {
          id
          body
          createdAt
          updatedAt
          author { login }
        }
      }

      # Review submissions (Approve / Request changes / Comment), with body if present
      reviews(first: 100, after: $reviewsCursor) {
        pageInfo { hasNextPage endCursor }
        nodes {
          id
          state
          body
          submittedAt
          author { login }
        }
      }

      # Inline review threads (grouped), includes resolved state
      reviewThreads(first: 100, after: $threadsCursor) {
        pageInfo { hasNextPage endCursor }
        nodes {
          id
          isResolved
          isOutdated
          path
          line
          diffSide
          startLine
          startDiffSide
          originalLine
          originalStartLine
          resolvedBy { login }
          comments(first: 100) {
            nodes {
              id
              body
              createdAt
              updatedAt
              author { login }
            }
          }
        }
      }
    }
  }
}
"""


def _run(cmd: list[str], stdin: str | None = None) -> str:
    p = subprocess.run(cmd, input=stdin, capture_output=True, text=True)
    if p.returncode != 0:
        raise RuntimeError(f"Command failed: {' '.join(cmd)}\n{p.stderr}")
    return p.stdout


def _run_json(cmd: list[str], stdin: str | None = None) -> dict[str, Any]:
    out = _run(cmd, stdin=stdin)
    try:
        return json.loads(out)
    except json.JSONDecodeError as e:
        raise RuntimeError(f"Failed to parse JSON from command output: {e}\nRaw:\n{out}") from e


def gh_pr_view_json(fields: str, pr: str | None = None, repo: str | None = None) -> dict[str, Any]:
    cmd = ["gh", "pr", "view"]
    if pr:
        cmd.append(pr)
    if repo:
        cmd += ["--repo", repo]
    cmd += ["--json", fields]
    return _run_json(cmd)


def split_repo(repo: str) -> tuple[str, str]:
    parts = repo.split("/", 1)
    if len(parts) != 2 or not all(parts):
        raise ValueError("--repo must be OWNER/REPO")
    return parts[0], parts[1]


def parse_pr_url(value: str) -> tuple[str, int] | None:
    match = re.fullmatch(r"https://github\.com/([^/]+/[^/]+)/pull/([1-9][0-9]*)", value)
    if not match:
        return None
    return match.group(1), int(match.group(2))


def resolve_pr_ref(pr_arg: str | None, repo_arg: str | None) -> tuple[str, str, int]:
    if pr_arg:
        url_ref = parse_pr_url(pr_arg)
        if url_ref:
            repo_arg, number = url_ref
            owner, repo = split_repo(repo_arg)
            return owner, repo, number
        if not re.fullmatch(r"[1-9][0-9]*", pr_arg):
            raise ValueError("--pr must be a PR number or GitHub pull request URL")
        if not repo_arg:
            raise ValueError("--repo is required when --pr is a number")
        owner, repo = split_repo(repo_arg)
        return owner, repo, int(pr_arg)

    pr = gh_pr_view_json("number,url", repo=repo_arg)
    url_ref = parse_pr_url(pr["url"])
    if not url_ref:
        raise ValueError("unable to resolve base repository from current branch PR URL")
    repo_arg, number = url_ref
    owner, repo = split_repo(repo_arg)
    return owner, repo, number


def gh_api_graphql(
    owner: str,
    repo: str,
    number: int,
    comments_cursor: str | None = None,
    reviews_cursor: str | None = None,
    threads_cursor: str | None = None,
) -> dict[str, Any]:
    """
    Call `gh api graphql` using -F variables, avoiding JSON blobs with nulls.
    Query is passed via stdin using query=@- to avoid shell newline/quoting issues.
    """
    cmd = [
        "gh",
        "api",
        "graphql",
        "-F",
        "query=@-",
        "-F",
        f"owner={owner}",
        "-F",
        f"repo={repo}",
        "-F",
        f"number={number}",
    ]
    if comments_cursor:
        cmd += ["-F", f"commentsCursor={comments_cursor}"]
    if reviews_cursor:
        cmd += ["-F", f"reviewsCursor={reviews_cursor}"]
    if threads_cursor:
        cmd += ["-F", f"threadsCursor={threads_cursor}"]

    return _run_json(cmd, stdin=QUERY)


def fetch_all(owner: str, repo: str, number: int) -> dict[str, Any]:
    conversation_comments: list[dict[str, Any]] = []
    reviews: list[dict[str, Any]] = []
    review_threads: list[dict[str, Any]] = []

    comments_cursor: str | None = None
    reviews_cursor: str | None = None
    threads_cursor: str | None = None

    pr_meta: dict[str, Any] | None = None

    while True:
        payload = gh_api_graphql(
            owner=owner,
            repo=repo,
            number=number,
            comments_cursor=comments_cursor,
            reviews_cursor=reviews_cursor,
            threads_cursor=threads_cursor,
        )

        if "errors" in payload and payload["errors"]:
            raise RuntimeError(f"GitHub GraphQL errors:\n{json.dumps(payload['errors'], indent=2)}")

        pr = payload["data"]["repository"]["pullRequest"]
        if pr_meta is None:
            pr_meta = {
                "number": pr["number"],
                "url": pr["url"],
                "title": pr["title"],
                "state": pr["state"],
                "owner": owner,
                "repo": repo,
            }

        c = pr["comments"]
        r = pr["reviews"]
        t = pr["reviewThreads"]

        conversation_comments.extend(c.get("nodes") or [])
        reviews.extend(r.get("nodes") or [])
        review_threads.extend(t.get("nodes") or [])

        comments_cursor = c["pageInfo"]["endCursor"] if c["pageInfo"]["hasNextPage"] else None
        reviews_cursor = r["pageInfo"]["endCursor"] if r["pageInfo"]["hasNextPage"] else None
        threads_cursor = t["pageInfo"]["endCursor"] if t["pageInfo"]["hasNextPage"] else None

        if not (comments_cursor or reviews_cursor or threads_cursor):
            break

    assert pr_meta is not None
    return {
        "pull_request": pr_meta,
        "conversation_comments": conversation_comments,
        "reviews": reviews,
        "review_threads": review_threads,
    }


def self_test() -> None:
    assert parse_pr_url("https://github.com/o/r/pull/12") == ("o/r", 12)
    assert parse_pr_url("https://github.com/o/r/issues/12") is None
    assert split_repo("owner/repo") == ("owner", "repo")
    assert resolve_pr_ref("7", "owner/repo") == ("owner", "repo", 7)
    assert resolve_pr_ref("https://github.com/owner/repo/pull/8", None) == ("owner", "repo", 8)
    try:
        resolve_pr_ref("7", None)
    except ValueError as exc:
        assert "--repo is required" in str(exc)
    else:
        raise AssertionError("numbered PR without repo should fail")


def main() -> None:
    parser = argparse.ArgumentParser(description="Fetch GitHub PR comments, reviews, and review threads.")
    parser.add_argument("--repo", help="Base repository as OWNER/REPO. Required when --pr is a number.")
    parser.add_argument("--pr", help="PR number or https://github.com/OWNER/REPO/pull/NUMBER URL.")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return

    try:
        if args.pr:
            owner, repo, number = resolve_pr_ref(args.pr, args.repo)
        else:
            owner, repo, number = resolve_pr_ref(None, args.repo)
    except ValueError as exc:
        raise SystemExit(str(exc)) from None
    result = fetch_all(owner, repo, number)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
