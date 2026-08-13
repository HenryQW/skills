#!/usr/bin/env python3
"""Resolve supplied GitHub review thread IDs after strict PR/head checks."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from fetch_feedback import SweepError, graphql, require_clean_head, resolve_metadata

RESOLVE_MUTATION = """\
mutation($threadId:ID!){resolveReviewThread(input:{threadId:$threadId}){thread{id isResolved}}}
"""
THREADS_QUERY = """\
query($owner:String!,$repo:String!,$number:Int!,$cursor:String){
  repository(owner:$owner,name:$repo){pullRequest(number:$number){
    reviewThreads(first:100,after:$cursor){pageInfo{hasNextPage endCursor} nodes{id isResolved}}
  }}
}
"""


def load_snapshot(path: str) -> dict[str, Any]:
    try:
        data = json.loads(Path(path).read_text())
        metadata = data["pull_request"]
        threads = data["review_threads"]
    except (OSError, json.JSONDecodeError, KeyError, TypeError) as error:
        raise SweepError(f"invalid feedback snapshot {path}: {error}") from error
    if not isinstance(metadata, dict) or not isinstance(threads, list):
        raise SweepError(f"invalid feedback snapshot {path}")
    return data


def require_current_head(snapshot: dict[str, Any], local_head: str) -> dict[str, Any]:
    previous = snapshot["pull_request"]
    current = resolve_metadata(previous["url"], None)
    if current["head_ref_oid"] != previous["head_ref_oid"]:
        raise SweepError(
            "PR head changed since feedback fetch: "
            f"{previous['head_ref_oid']} -> {current['head_ref_oid']}"
        )
    if current["head_ref_oid"] != local_head:
        raise SweepError(
            f"local HEAD {local_head} does not match PR head {current['head_ref_oid']}"
        )
    return current


def fetch_thread_states(metadata: dict[str, Any]) -> dict[str, bool]:
    owner, repo = metadata["base_repository"].split("/", 1)
    states: dict[str, bool] = {}
    cursor: str | None = None
    while True:
        payload = graphql(
            THREADS_QUERY,
            owner=owner,
            repo=repo,
            number=metadata["number"],
            cursor=cursor,
        )
        pull_request = payload["data"]["repository"]["pullRequest"]
        if not pull_request:
            raise SweepError("pull request disappeared")
        connection = pull_request["reviewThreads"]
        states.update({thread["id"]: thread["isResolved"] for thread in connection.get("nodes") or []})
        if not connection["pageInfo"].get("hasNextPage"):
            return states
        cursor = connection["pageInfo"].get("endCursor")
        if not cursor:
            raise SweepError("missing review thread pagination cursor")


def resolve_threads(snapshot: dict[str, Any], thread_ids: list[str]) -> int:
    local_head = require_clean_head()
    metadata = require_current_head(snapshot, local_head)
    known = {thread["id"] for thread in snapshot["review_threads"]}
    requested = list(dict.fromkeys(thread_ids))
    unknown = sorted(set(requested) - known)
    if unknown:
        raise SweepError(f"thread IDs absent from feedback snapshot: {unknown}")

    for thread_id in requested:
        payload = graphql(RESOLVE_MUTATION, threadId=thread_id)
        thread = payload["data"]["resolveReviewThread"]["thread"]
        if thread.get("id") != thread_id:
            raise SweepError(f"GitHub returned wrong thread for {thread_id}")

    states = fetch_thread_states(metadata)
    missing = [thread_id for thread_id in requested if thread_id not in states]
    unresolved = [thread_id for thread_id in requested if states.get(thread_id) is False]
    if missing or unresolved:
        raise SweepError(f"resolution verification failed: missing={missing}, unresolved={unresolved}")
    return len(requested)


def self_test() -> None:
    def page(nodes: list[dict[str, Any]], more: bool = False, cursor: str | None = None) -> dict[str, Any]:
        return {"nodes": nodes, "pageInfo": {"hasNextPage": more, "endCursor": cursor}}

    mutations: list[str] = []
    pages = 0

    def fake_graphql(query: str, **variables: Any) -> dict[str, Any]:
        nonlocal pages
        if query == RESOLVE_MUTATION:
            mutations.append(variables["threadId"])
            return {"data": {"resolveReviewThread": {"thread": {
                "id": variables["threadId"], "isResolved": True,
            }}}}
        pages += 1
        nodes = [{"id": "t1", "isResolved": True}] if pages == 1 else [{"id": "t2", "isResolved": True}]
        return {"data": {"repository": {"pullRequest": {
            "reviewThreads": page(nodes, pages == 1, "next"),
        }}}}

    originals = {name: globals()[name] for name in ("graphql", "require_clean_head", "require_current_head")}
    try:
        globals()["graphql"] = fake_graphql
        globals()["require_clean_head"] = lambda: "abc"
        globals()["require_current_head"] = lambda _snapshot, head: (
            {"base_repository": "o/r", "number": 1} if head == "abc" else None
        )
        count = resolve_threads(
            {"pull_request": {}, "review_threads": [{"id": "t1"}, {"id": "t2"}]},
            ["t1", "t2", "t1"],
        )
    finally:
        globals().update(originals)
    assert count == 2
    assert mutations == ["t1", "t2"]
    assert pages == 2


def main(argv: list[str]) -> int:
    if argv == ["--self-test"]:
        self_test()
        return 0
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--snapshot", required=True, help="output from fetch_feedback.py")
    parser.add_argument("thread_ids", nargs="+")
    args = parser.parse_args(argv)
    try:
        count = resolve_threads(load_snapshot(args.snapshot), args.thread_ids)
        print(f"resolved={count} verified={count}")
    except SweepError as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
