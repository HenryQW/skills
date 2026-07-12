#!/usr/bin/env python3
"""Encode and decode Issue Blueprint's embedded issue graph contract."""

from __future__ import annotations

import json
import re

from issue_plan import ordered_issues, validate as validate_plan


GRAPH_VERSION = 1
GRAPH_RE = re.compile(r"<!--\s*issue-plan-graph\s*\n(.*?)\n-->", re.DOTALL)


def graph_payload(plan: dict, numbers: dict[str, str]) -> dict:
    validate_plan(plan)
    required = {"tracker", *(issue["id"] for issue in plan["issues"])}
    missing = required - set(numbers)
    if missing:
        raise SystemExit(f"graph payload missing issue numbers: {sorted(missing)}")

    def number(issue_id: str) -> int:
        value = numbers[issue_id]
        if not isinstance(value, str) or not re.fullmatch(r"#[1-9][0-9]*", value):
            raise SystemExit(f"invalid issue number for {issue_id}: {value!r}")
        return int(value[1:])

    return {
        "version": GRAPH_VERSION,
        "tracker": number("tracker"),
        "issues": [
            {
                "id": issue["id"],
                "number": number(issue["id"]),
                "role": issue.get("role", "implementation"),
                "blocked_by": [number(item) for item in issue.get("blocked_by", [])],
                "blocks": [number(item) for item in issue.get("blocks", [])],
            }
            for issue in ordered_issues(plan)
        ],
    }


def validate_graph(graph: object) -> dict:
    if not isinstance(graph, dict):
        raise SystemExit("malformed issue-plan-graph payload: expected an object")
    version = graph.get("version")
    if version != GRAPH_VERSION:
        raise SystemExit(f"unsupported issue-plan-graph version: {version!r}")
    if not isinstance(graph.get("tracker"), int) or graph["tracker"] < 1:
        raise SystemExit("malformed issue-plan-graph payload: tracker must be a positive integer")
    issues = graph.get("issues")
    if not isinstance(issues, list) or not issues:
        raise SystemExit("malformed issue-plan-graph payload: issues must be a non-empty list")

    numbers: set[int] = set()
    ids: set[str] = set()
    for index, issue in enumerate(issues):
        if not isinstance(issue, dict):
            raise SystemExit(f"malformed issue-plan-graph payload: issues[{index}] must be an object")
        if not isinstance(issue.get("id"), str) or not issue["id"]:
            raise SystemExit(f"malformed issue-plan-graph payload: issues[{index}].id is required")
        number = issue.get("number")
        if not isinstance(number, int) or number < 1:
            raise SystemExit(f"malformed issue-plan-graph payload: issues[{index}].number must be a positive integer")
        if issue["id"] in ids or number in numbers:
            raise SystemExit("malformed issue-plan-graph payload: duplicate issue id or number")
        ids.add(issue["id"])
        numbers.add(number)
        for key in ("blocked_by", "blocks"):
            refs = issue.get(key)
            if not isinstance(refs, list) or any(not isinstance(ref, int) or ref < 1 for ref in refs):
                raise SystemExit(f"malformed issue-plan-graph payload: issues[{index}].{key} must contain positive integers")
    for issue in issues:
        unknown = (set(issue["blocked_by"]) | set(issue["blocks"])) - numbers
        if unknown:
            raise SystemExit(f"malformed issue-plan-graph payload: unknown issue references {sorted(unknown)}")
    return graph


def encode(plan: dict, numbers: dict[str, str]) -> str:
    return json.dumps(graph_payload(plan, numbers), separators=(",", ":"), sort_keys=True)


def embed(plan: dict, numbers: dict[str, str]) -> str:
    return f"<!-- issue-plan-graph\n{encode(plan, numbers)}\n-->"


def extract(body: str) -> str:
    match = GRAPH_RE.search(body or "")
    if not match:
        raise SystemExit("parent issue is missing issue-plan-graph payload")
    return match.group(1)


def decode(payload: str) -> dict:
    try:
        graph = json.loads(payload)
    except json.JSONDecodeError as error:
        raise SystemExit(f"malformed issue-plan-graph payload: {error.msg}") from error
    return validate_graph(graph)


def decode_embedded(body: str) -> dict:
    return decode(extract(body))


def self_test() -> None:
    plan = {
        "tracker": {"title": "T", "goal": "G", "constraints": [], "non_goals": [], "definition_of_done": []},
        "issues": [
            {"id": "a", "title": "A", "purpose": "A.", "acceptance": ["A."], "testing": {"seam": "API", "validation": "python test.py", "do_not_test": "internals"}, "blocked_by": [], "blocks": ["b"], "parallelism": "First."},
            {"id": "b", "title": "B", "role": "final_check", "purpose": "B.", "acceptance": ["B."], "testing": {"seam": "integration", "validation": "python test.py", "do_not_test": "internals"}, "blocked_by": ["a"], "blocks": [], "parallelism": "Last."},
        ],
        "waves": [{"name": "First", "items": ["a"]}, {"name": "Last", "items": ["b"]}],
    }
    body = embed(plan, {"tracker": "#10", "a": "#11", "b": "#12"})
    graph = decode_embedded(body)
    assert graph["tracker"] == 10
    assert graph["issues"][1]["blocked_by"] == [11]
    for candidate, expected in (
        ("", "missing issue-plan-graph"),
        ("<!-- issue-plan-graph\n{bad}\n-->", "malformed issue-plan-graph"),
        ('<!-- issue-plan-graph\n{"version":2}\n-->', "unsupported issue-plan-graph version"),
        ('<!-- issue-plan-graph\n{"issues":[],"tracker":10,"version":1}\n-->', "issues must be a non-empty list"),
        ('<!-- issue-plan-graph\n{"issues":[{"blocked_by":[99],"blocks":[],"id":"a","number":11}],"tracker":10,"version":1}\n-->', "unknown issue references"),
    ):
        try:
            decode_embedded(candidate)
        except SystemExit as error:
            assert expected in str(error)
        else:
            raise AssertionError(f"expected graph error containing {expected!r}")


if __name__ == "__main__":
    self_test()
