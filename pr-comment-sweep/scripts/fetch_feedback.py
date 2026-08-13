#!/usr/bin/env python3
"""Fetch complete GitHub PR conversation, review, thread, and reply data."""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, Sequence

PR_FIELDS = "number,url,title,state,baseRefName,headRefName,headRefOid,headRepository"
PR_URL = re.compile(r"https://github\.com/([^/]+/[^/]+)/pull/([1-9][0-9]*)")
FEEDBACK_QUERY = """\
query($owner:String!,$repo:String!,$number:Int!,$commentsCursor:String,$reviewsCursor:String,$threadsCursor:String){
  repository(owner:$owner,name:$repo){pullRequest(number:$number){
    comments(first:100,after:$commentsCursor){pageInfo{hasNextPage endCursor} nodes{id url body createdAt author{login}}}
    reviews(first:100,after:$reviewsCursor){pageInfo{hasNextPage endCursor} nodes{id url state body submittedAt author{login}}}
    reviewThreads(first:100,after:$threadsCursor){pageInfo{hasNextPage endCursor} nodes{
      id isResolved isOutdated path line diffSide startLine startDiffSide originalLine originalStartLine
      comments(first:100){pageInfo{hasNextPage endCursor} nodes{id url body createdAt author{login}}}
    }}
  }}
}
"""
THREAD_COMMENTS_QUERY = """\
query($threadId:ID!,$cursor:String){node(id:$threadId){... on PullRequestReviewThread{
  comments(first:100,after:$cursor){pageInfo{hasNextPage endCursor} nodes{id url body createdAt author{login}}}
}}}
"""


class SweepError(RuntimeError):
    pass


def run(command: Sequence[str], stdin: str | None = None) -> str:
    result = subprocess.run(command, input=stdin, text=True, capture_output=True)
    if result.returncode:
        detail = (result.stderr or result.stdout).strip()
        raise SweepError(f"command failed: {' '.join(command)}\n{detail}")
    return result.stdout


def run_json(command: Sequence[str], stdin: str | None = None) -> dict[str, Any]:
    output = run(command, stdin)
    try:
        value = json.loads(output)
    except json.JSONDecodeError as error:
        raise SweepError(f"invalid JSON from {' '.join(command)}: {error}") from error
    if not isinstance(value, dict):
        raise SweepError(f"unexpected JSON from {' '.join(command)}")
    return value


def git(*args: str) -> str:
    return run(("git", *args)).strip()


def require_gh() -> None:
    if shutil.which("gh") is None:
        raise SweepError("gh is not installed or not on PATH")
    run(("gh", "auth", "status"))


def require_clean_head() -> str:
    require_gh()
    git("rev-parse", "--show-toplevel")
    if git("status", "--porcelain"):
        raise SweepError("index and worktree must be clean")
    return git("rev-parse", "HEAD")


def parse_pr_url(url: str) -> tuple[str, int]:
    match = PR_URL.fullmatch(url)
    if not match:
        raise SweepError(f"unsupported pull request URL: {url}")
    return match.group(1), int(match.group(2))


def head_repository_name(value: Any) -> str:
    if isinstance(value, dict) and value.get("nameWithOwner"):
        return str(value["nameWithOwner"])
    raise SweepError("PR head repository identity is unavailable")


def resolve_metadata(pr: str | None, repo: str | None) -> dict[str, Any]:
    if pr and pr.isdigit() and not repo:
        raise SweepError("--repo is required when --pr is a number")
    command = ["gh", "pr", "view"]
    if pr:
        command.append(pr)
    if repo:
        command.extend(("--repo", repo))
    command.extend(("--json", PR_FIELDS))
    data = run_json(command)
    if data.get("state") != "OPEN":
        raise SweepError(f"PR must be OPEN, got {data.get('state')!r}")
    base_repository, url_number = parse_pr_url(str(data.get("url", "")))
    return {
        "number": int(data.get("number") or url_number),
        "url": data["url"],
        "title": data.get("title", ""),
        "state": data["state"],
        "base_ref_name": data.get("baseRefName", ""),
        "head_ref_name": data.get("headRefName", ""),
        "head_ref_oid": data.get("headRefOid", ""),
        "head_repository": head_repository_name(data.get("headRepository")),
        "base_repository": base_repository,
        "selection": "supplied" if pr else "current-branch",
    }


def require_matching_head(metadata: dict[str, Any], local_head: str, check_branch: bool) -> None:
    if metadata["head_ref_oid"] != local_head:
        raise SweepError(
            f"local HEAD {local_head} does not match PR head {metadata['head_ref_oid']}"
        )
    if check_branch:
        branch = git("branch", "--show-current")
        if branch != metadata["head_ref_name"]:
            raise SweepError(
                f"local branch {branch!r} does not match PR head branch {metadata['head_ref_name']!r}"
            )


def graphql(query: str, **variables: Any) -> dict[str, Any]:
    command = ["gh", "api", "graphql", "-F", "query=@-"]
    for key, value in variables.items():
        if value is not None:
            command.extend(("-F", f"{key}={value}"))
    payload = run_json(command, query)
    if payload.get("errors"):
        raise SweepError(f"GitHub GraphQL errors: {json.dumps(payload['errors'])}")
    return payload


def fetch_thread_replies(thread: dict[str, Any]) -> list[dict[str, Any]]:
    connection = thread.pop("comments")
    comments = list(connection.get("nodes") or [])
    while connection["pageInfo"].get("hasNextPage"):
        cursor = connection["pageInfo"].get("endCursor")
        if not cursor:
            raise SweepError(f"missing reply cursor for thread {thread['id']}")
        payload = graphql(THREAD_COMMENTS_QUERY, threadId=thread["id"], cursor=cursor)
        node = payload["data"]["node"]
        if not node:
            raise SweepError(f"review thread disappeared: {thread['id']}")
        connection = node["comments"]
        comments.extend(connection.get("nodes") or [])
    return comments


def fetch_feedback(metadata: dict[str, Any]) -> dict[str, Any]:
    owner, repo = metadata["base_repository"].split("/", 1)
    targets: dict[str, list[dict[str, Any]]] = {
        "comments": [],
        "reviews": [],
        "threads": [],
    }
    cursors: dict[str, str | None] = {name: None for name in targets}
    done = {name: False for name in targets}
    keys = {"comments": "comments", "reviews": "reviews", "threads": "reviewThreads"}

    while not all(done.values()):
        payload = graphql(
            FEEDBACK_QUERY,
            owner=owner,
            repo=repo,
            number=metadata["number"],
            commentsCursor=cursors["comments"],
            reviewsCursor=cursors["reviews"],
            threadsCursor=cursors["threads"],
        )
        pull_request = payload["data"]["repository"]["pullRequest"]
        if not pull_request:
            raise SweepError("pull request disappeared")
        for name, target in targets.items():
            if done[name]:
                continue
            connection = pull_request[keys[name]]
            target.extend(connection.get("nodes") or [])
            done[name] = not connection["pageInfo"].get("hasNextPage")
            cursors[name] = connection["pageInfo"].get("endCursor")
            if not done[name] and not cursors[name]:
                raise SweepError(f"missing pagination cursor for {name}")

    for thread in targets["threads"]:
        thread["comments"] = fetch_thread_replies(thread)
    return {
        "pull_request": metadata,
        "conversation_comments": targets["comments"],
        "reviews": targets["reviews"],
        "review_threads": targets["threads"],
    }


def write_feedback(data: dict[str, Any], output: str) -> None:
    serialized = json.dumps(data, separators=(",", ":"))
    if output == "-":
        print(serialized)
        return
    path = Path(output).expanduser().resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(serialized + "\n")
    threads = data["review_threads"]
    unresolved = sum(not thread["isResolved"] for thread in threads)
    print(
        f"feedback={path} comments={len(data['conversation_comments'])} "
        f"reviews={len(data['reviews'])} threads={len(threads)} unresolved={unresolved}"
    )


def self_test() -> None:
    assert parse_pr_url("https://github.com/o/r/pull/12") == ("o/r", 12)
    def page(nodes: list[dict[str, Any]], more: bool = False, cursor: str | None = None) -> dict[str, Any]:
        return {"nodes": nodes, "pageInfo": {"hasNextPage": more, "endCursor": cursor}}
    calls = 0

    def fake_graphql(query: str, **_variables: Any) -> dict[str, Any]:
        nonlocal calls
        calls += 1
        if query == THREAD_COMMENTS_QUERY:
            return {"data": {"node": {"comments": page([{"id": "reply-101"}])}}}
        thread = {
            "id": "t1",
            "isResolved": False,
            "comments": page([{"id": f"reply-{n}"} for n in range(1, 101)], True, "next"),
        }
        return {"data": {"repository": {"pullRequest": {
            "comments": page([{"id": "c1"}]),
            "reviews": page([{"id": f"r{calls}"}], calls == 1, f"r{calls}"),
            "reviewThreads": page([thread]),
        }}}}

    original = globals()["graphql"]
    try:
        globals()["graphql"] = fake_graphql
        result = fetch_feedback({"base_repository": "o/r", "number": 1})
    finally:
        globals()["graphql"] = original
    assert [item["id"] for item in result["reviews"]] == ["r1", "r2"]
    assert len(result["review_threads"][0]["comments"]) == 101
    assert result["review_threads"][0]["comments"][-1]["id"] == "reply-101"


def main(argv: list[str]) -> int:
    if argv == ["--self-test"]:
        self_test()
        return 0
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", help="OWNER/REPO; required when --pr is a number")
    parser.add_argument("--pr", help="PR number or URL; defaults to current branch PR")
    parser.add_argument("--output", required=True, help="snapshot path, or - for stdout")
    args = parser.parse_args(argv)
    try:
        local_head = require_clean_head()
        metadata = resolve_metadata(args.pr, args.repo)
        require_matching_head(metadata, local_head, not args.pr)
        feedback = fetch_feedback(metadata)
        current = resolve_metadata(metadata["url"], None)
        require_matching_head(current, local_head, False)
        write_feedback(feedback, args.output)
    except SweepError as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
