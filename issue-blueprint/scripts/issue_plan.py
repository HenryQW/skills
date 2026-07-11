#!/usr/bin/env python3
"""Load, validate, and order issue plans."""

from __future__ import annotations

import json
import re
from pathlib import Path


GRAPH_VERSION = 1
ID_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")


def load_plan(path: Path) -> dict:
    plan = json.loads(path.read_text())
    validate(plan)
    return plan


def validate_testing(issue: dict) -> None:
    testing = issue.get("testing")
    issue_id = issue.get("id", "<unknown>")
    if not isinstance(testing, dict):
        raise SystemExit(f"{issue_id}.testing is required")
    required = ("seam", "validation", "do_not_test")
    missing = [key for key in required if not str(testing.get(key, "")).strip()]
    if missing:
        raise SystemExit(f"{issue_id}.testing missing {', '.join(missing)}")
    if testing.get("seam") == "Not specified" or testing.get("validation") == "Not specified":
        raise SystemExit(f"{issue_id}.testing must be explicit")


def validate(plan: dict) -> None:
    tracker = plan.get("tracker")
    if not isinstance(tracker, dict):
        raise SystemExit("tracker is required")
    for key in ("title", "goal"):
        if not isinstance(tracker.get(key), str) or not tracker[key].strip():
            raise SystemExit(f"tracker.{key} is required")
    for key in ("constraints", "non_goals", "definition_of_done"):
        values = tracker.get(key)
        if not isinstance(values, list) or any(not isinstance(item, str) or not item.strip() for item in values):
            raise SystemExit(f"tracker.{key} must be a list of non-empty strings")

    issues = plan.get("issues")
    if not isinstance(issues, list) or not issues:
        raise SystemExit("issues must be a non-empty list")
    for index, issue in enumerate(issues, 1):
        if not isinstance(issue, dict):
            raise SystemExit(f"issues[{index}] must be an object")
        issue_id = issue.get("id")
        if not isinstance(issue_id, str) or not issue_id:
            raise SystemExit(f"issues[{index}].id is required")
        for key in ("title", "purpose", "parallelism"):
            if not isinstance(issue.get(key), str) or not issue[key].strip():
                raise SystemExit(f"{issue_id}.{key} is required")
        acceptance = issue.get("acceptance")
        if not isinstance(acceptance, list) or not acceptance or any(not isinstance(item, str) or not item.strip() for item in acceptance):
            raise SystemExit(f"{issue_id}.acceptance must be a non-empty list")
        for key in ("blocked_by", "blocks"):
            values = issue.get(key)
            if not isinstance(values, list) or any(not isinstance(item, str) or not item for item in values):
                raise SystemExit(f"{issue_id}.{key} must be a list of issue IDs")

    ids = [item["id"] for item in issues]
    if len(ids) != len(set(ids)):
        raise SystemExit("duplicate issue id")
    bad_ids = [item for item in ids if not ID_RE.match(item)]
    if bad_ids:
        raise SystemExit(f"invalid issue id: {bad_ids}")
    known = set(ids)
    by_id = {issue["id"]: issue for issue in issues}
    final = final_check(plan)
    final_id = final["id"]
    non_final = known - {final_id}
    if set(final.get("blocked_by", [])) != non_final:
        raise SystemExit(f"{final_id} must be blocked by every non-final issue")
    if final.get("blocks"):
        raise SystemExit(f"{final_id} final_check must not block other issues")
    for issue in issues:
        issue_id = issue["id"]
        validate_testing(issue)
        for key in ("blocked_by", "blocks"):
            deps = set(issue.get(key, []))
            if issue_id in deps:
                raise SystemExit(f"{issue_id} cannot depend on itself")
            missing = deps - known
            if missing:
                raise SystemExit(f"{issue_id} has unknown {key}: {sorted(missing)}")
        for blocker in issue.get("blocked_by", []):
            if issue_id not in by_id[blocker].get("blocks", []):
                raise SystemExit(f"{issue_id} blocked_by {blocker}, but {blocker}.blocks is missing {issue_id}")
        for blocked in issue.get("blocks", []):
            if issue_id not in by_id[blocked].get("blocked_by", []):
                raise SystemExit(f"{issue_id} blocks {blocked}, but {blocked}.blocked_by is missing {issue_id}")
    ordered_issues(plan)
    waves = plan.get("waves")
    if not isinstance(waves, list) or not waves:
        raise SystemExit("waves must be a non-empty list")
    seen: set[str] = set()
    for index, wave in enumerate(waves, 1):
        if not isinstance(wave, dict) or not isinstance(wave.get("name"), str) or not wave["name"].strip():
            raise SystemExit(f"waves[{index}].name is required")
        items = wave.get("items", [])
        if not isinstance(items, list) or not items or any(not isinstance(item, str) or not item for item in items):
            raise SystemExit(f"{wave['name']}.items must be a non-empty list of issue IDs")
        if len(items) != len(set(items)) or set(items) & seen:
            raise SystemExit(f"{wave['name']} repeats issue membership")
        missing = set(items) - known
        if missing:
            raise SystemExit(f"{wave['name']} has unknown items: {sorted(missing)}")
        for item in items:
            blockers = set(by_id[item].get("blocked_by", []))
            if not blockers <= seen:
                raise SystemExit(f"{wave['name']} schedules {item} before blockers {sorted(blockers - seen)}")
        seen.update(items)
    if seen != known:
        raise SystemExit(f"waves omit issues: {sorted(known - seen)}")
    for index, item in enumerate(plan.get("dropped_findings", []), 1):
        if not item.get("finding") or not item.get("reason"):
            raise SystemExit(f"dropped_findings[{index}] requires finding and reason")


def ordered_issues(plan: dict) -> list[dict]:
    remaining = {issue["id"]: issue for issue in plan["issues"]}
    ordered: list[dict] = []
    done: set[str] = set()
    while remaining:
        ready = [issue for issue in plan["issues"] if issue["id"] in remaining and set(issue.get("blocked_by", [])) <= done]
        if not ready:
            raise SystemExit(f"dependency cycle: {sorted(remaining)}")
        for issue in ready:
            ordered.append(issue)
            done.add(issue["id"])
            remaining.pop(issue["id"])
    return ordered


def final_check(plan: dict) -> dict:
    matches = [issue for issue in plan["issues"] if issue.get("role") == "final_check"]
    if len(matches) != 1:
        raise SystemExit("exactly one issue must have role final_check")
    return matches[0]


def graph_payload(plan: dict, numbers: dict[str, str]) -> dict:
    validate(plan)
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


def embedded_graph(plan: dict, numbers: dict[str, str]) -> str:
    payload = json.dumps(graph_payload(plan, numbers), separators=(",", ":"), sort_keys=True)
    return f"<!-- issue-plan-graph\n{payload}\n-->"
