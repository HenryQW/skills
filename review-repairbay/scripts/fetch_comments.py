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
import os
import sys
from pathlib import Path
from typing import Any


SKILLS_ROOT = Path(os.environ.get("SKILLS_ROOT") or Path(__file__).resolve().parents[2])
ADAPTER_SCRIPTS = SKILLS_ROOT / "github-adapter" / "scripts"
if not ADAPTER_SCRIPTS.is_dir():
    raise SystemExit(f"github-adapter not found: {ADAPTER_SCRIPTS}")
sys.path.insert(0, str(ADAPTER_SCRIPTS))

from github_adapter import GitHub, GitHubError  # noqa: E402


GITHUB = GitHub()

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
          comments(first: 100) {
            nodes {
              id
              body
              createdAt
              author { login }
            }
          }
        }
      }
    }
  }
}
"""


def fetch_page(
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
    return GITHUB.graphql(
        QUERY,
        {
            "owner": owner,
            "repo": repo,
            "number": number,
            "commentsCursor": comments_cursor,
            "reviewsCursor": reviews_cursor,
            "threadsCursor": threads_cursor,
        },
    )


def fetch_all(owner: str, repo: str, number: int) -> dict[str, Any]:
    conversation_comments: list[dict[str, Any]] = []
    reviews: list[dict[str, Any]] = []
    review_threads: list[dict[str, Any]] = []

    comments_cursor: str | None = None
    reviews_cursor: str | None = None
    threads_cursor: str | None = None
    comments_done = False
    reviews_done = False
    threads_done = False

    pr_meta: dict[str, Any] | None = None

    while True:
        payload = fetch_page(
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

        if not comments_done:
            conversation_comments.extend(c.get("nodes") or [])
            comments_done = not c["pageInfo"]["hasNextPage"]
            comments_cursor = c["pageInfo"]["endCursor"]
        if not reviews_done:
            reviews.extend(r.get("nodes") or [])
            reviews_done = not r["pageInfo"]["hasNextPage"]
            reviews_cursor = r["pageInfo"]["endCursor"]
        if not threads_done:
            review_threads.extend(t.get("nodes") or [])
            threads_done = not t["pageInfo"]["hasNextPage"]
            threads_cursor = t["pageInfo"]["endCursor"]

        if comments_done and reviews_done and threads_done:
            break

    assert pr_meta is not None
    return {
        "pull_request": pr_meta,
        "conversation_comments": conversation_comments,
        "reviews": reviews,
        "review_threads": review_threads,
    }


def self_test() -> None:
    page = lambda nodes, has_next, cursor: {"nodes": nodes, "pageInfo": {"hasNextPage": has_next, "endCursor": cursor}}
    calls = 0

    def fake_graphql(*_args: Any, **_kwargs: Any) -> dict[str, Any]:
        nonlocal calls
        calls += 1
        review_nodes = [{"id": "r1"}] if calls == 1 else [{"id": "r2"}]
        return {"data": {"repository": {"pullRequest": {
            "number": 1, "url": "https://github.com/o/r/pull/1", "title": "PR", "state": "OPEN",
            "comments": page([{"id": "c1"}], False, "c1"),
            "reviews": page(review_nodes, calls == 1, f"r{calls}"),
            "reviewThreads": page([{"id": "t1"}], False, "t1"),
        }}}}

    original_fetch_page = fetch_page
    try:
        globals()["fetch_page"] = fake_graphql
        fetched = fetch_all("o", "r", 1)
    finally:
        globals()["fetch_page"] = original_fetch_page
    assert [node["id"] for node in fetched["conversation_comments"]] == ["c1"]
    assert [node["id"] for node in fetched["reviews"]] == ["r1", "r2"]
    assert [node["id"] for node in fetched["review_threads"]] == ["t1"]


def main() -> None:
    parser = argparse.ArgumentParser(description="Fetch GitHub PR comments, reviews, and review threads.")
    parser.add_argument("--repo", help="Base repository as OWNER/REPO. Defaults to the current repository.")
    parser.add_argument("--pr", help="PR number or https://github.com/OWNER/REPO/pull/NUMBER URL.")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return

    try:
        GITHUB.authenticate()
        reference = GITHUB.resolve_pr(args.pr, args.repo)
    except (GitHubError, ValueError) as exc:
        raise SystemExit(str(exc)) from None
    result = fetch_all(reference.owner, reference.name, reference.number)
    print(json.dumps(result, separators=(",", ":")))


if __name__ == "__main__":
    main()
