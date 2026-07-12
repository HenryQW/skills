#!/usr/bin/env python3
"""Inspect a shipyard parent issue and print a compact execution plan."""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Callable


SKILLS_ROOT = Path(os.environ.get("SKILLS_ROOT") or Path(__file__).resolve().parents[2])
BLUEPRINT_SCRIPTS = SKILLS_ROOT / "issue-blueprint" / "scripts"
ADAPTER_SCRIPTS = SKILLS_ROOT / "github-adapter" / "scripts"
if not BLUEPRINT_SCRIPTS.is_dir():
    raise SystemExit(f"issue-blueprint contract not found: {BLUEPRINT_SCRIPTS}")
if not ADAPTER_SCRIPTS.is_dir():
    raise SystemExit(f"github-adapter not found: {ADAPTER_SCRIPTS}")
sys.path.insert(0, str(BLUEPRINT_SCRIPTS))
sys.path.insert(0, str(ADAPTER_SCRIPTS))

from issue_graph_contract import decode_embedded  # noqa: E402
from github_adapter import GitHub, GitHubError  # noqa: E402


GITHUB = GitHub()


def run(command: list[str]) -> str:
    return subprocess.check_output(command, text=True).strip()


def child_from_issue(issue: dict[str, Any], graph_issue: dict[str, Any]) -> dict[str, Any]:
    return {
        "number": str(issue["number"]),
        "title": issue.get("title", ""),
        "state": issue.get("state", ""),
        "url": issue.get("url", ""),
        "blocked_by": [str(number) for number in graph_issue["blocked_by"]],
        "blocks": [str(number) for number in graph_issue["blocks"]],
        "final_check": graph_issue.get("role") == "final_check",
        "closing_prs": normalize_prs(issue.get("closedByPullRequestsReferences")),
    }


def normalize_prs(value: Any) -> list[dict[str, Any]]:
    if isinstance(value, dict):
        value = value.get("nodes") or []
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, dict)]


def pr_is_merged_to_base(pr: dict[str, Any], default_branch: str) -> bool:
    merged = bool(pr.get("merged") or pr.get("mergedAt") or pr.get("state") == "MERGED")
    base = pr.get("baseRefName")
    return merged and (not base or base == default_branch)


def has_pending_pr(child: dict[str, Any], default_branch: str) -> bool:
    return any(not pr_is_merged_to_base(pr, default_branch) for pr in child["closing_prs"])


def local_branch_merged(child_number: str, current_branch: str) -> bool:
    branch = f"refs/heads/issue-{child_number}"
    return bool(run(["git", "for-each-ref", f"--merged={current_branch}", "--format=%(refname)", branch, f"{branch}-*"]))


def local_done_numbers(
    children: list[dict[str, Any]],
    current_branch: str,
    mode: str,
    merged: Callable[[str, str], bool] = local_branch_merged,
) -> set[str]:
    if mode != "integration":
        return set()
    return {child["number"] for child in children if merged(child["number"], current_branch)}


def branch_mode(current_branch: str, default_branch: str) -> str:
    return "default_branch_blocked" if current_branch == default_branch else "integration"


def graph_errors(children: list[dict[str, Any]]) -> list[str]:
    errors: list[str] = []
    if not children:
        errors.append("parent issue does not reference any child issues")
    final_checks = [child["number"] for child in children if child["final_check"]]
    if len(final_checks) != 1:
        errors.append(f"expected exactly one final_check child, found {len(final_checks)}")
    return errors


def child_is_done(child: dict[str, Any], default_branch: str) -> bool:
    return child["state"] == "CLOSED" and not has_pending_pr(child, default_branch)


def classify(children: list[dict[str, Any]], default_branch: str, local_done: set[str] | None = None) -> list[dict[str, Any]]:
    local_done = local_done or set()
    by_number = {child["number"]: child for child in children}
    for child in children:
        blockers = [by_number.get(number) for number in child["blocked_by"]]
        missing = [number for number, blocker in zip(child["blocked_by"], blockers) if blocker is None]
        open_blockers = [
            blocker["number"]
            for blocker in blockers
            if blocker and blocker["number"] not in local_done and not child_is_done(blocker, default_branch)
        ]
        pending_pr = has_pending_pr(child, default_branch)
        if child["number"] in local_done:
            status = "done-local"
        elif child_is_done(child, default_branch):
            status = "done"
        elif pending_pr:
            status = "pending-pr"
        elif missing:
            status = "blocked-missing"
        elif open_blockers:
            status = "blocked"
        elif child["final_check"] and any(
            other["number"] != child["number"]
            and other["number"] not in local_done
            and not child_is_done(other, default_branch)
            for other in children
        ):
            status = "blocked-final-check"
        else:
            status = "runnable"
        child["status"] = status
        child["open_blockers"] = open_blockers
        child["missing_blockers"] = missing
        child["pending_prs"] = [pr.get("url") or f"#{pr.get('number')}" for pr in child["closing_prs"] if not pr_is_merged_to_base(pr, default_branch)]
    return children


def inspect(parent_issue: str, repo: str | None) -> dict[str, Any]:
    parent_ref = GITHUB.resolve_issue(parent_issue, repo)
    parent = GITHUB.issue_json(
        parent_ref.number,
        "number,title,url,body,state",
        parent_ref.repository,
    )
    graph = decode_embedded(parent.get("body") or "")
    if graph["tracker"] != parent["number"]:
        raise SystemExit(f"issue-plan-graph tracker #{graph['tracker']} does not match parent #{parent['number']}")
    children = [
        child_from_issue(
            GITHUB.issue_json(
                str(graph_issue["number"]),
                "number,title,url,state,closedByPullRequestsReferences",
                parent_ref.repository,
            ),
            graph_issue,
        )
        for graph_issue in graph["issues"]
    ]
    default_branch = GITHUB.default_branch(parent_ref.repository)
    current_branch = run(["git", "branch", "--show-current"])
    if not current_branch:
        raise SystemExit("detached HEAD is not supported")
    mode = branch_mode(current_branch, default_branch)
    local_done = local_done_numbers(children, current_branch, mode)
    plan = {
        "parent": {
            "number": str(parent["number"]),
            "title": parent.get("title", ""),
            "state": parent.get("state", ""),
            "url": parent.get("url", ""),
        },
        "default_branch": default_branch,
        "current_branch": current_branch,
        "mode": mode,
        "children": classify(children, default_branch, local_done),
    }
    if mode == "default_branch_blocked":
        plan["blocked_reason"] = "shipyard requires a non-default integration branch"
    return plan


def print_text(plan: dict[str, Any]) -> None:
    parent = plan["parent"]
    print(f"Parent: #{parent['number']} {parent['title']}")
    print(f"URL: {parent['url']}")
    print(f"Mode: {plan['mode']} ({plan['current_branch']} vs {plan['default_branch']})")
    if plan.get("blocked_reason"):
        print(f"Blocked: {plan['blocked_reason']}")
    print("\nChildren:")
    for child in plan["children"]:
        blockers = ", ".join(f"#{number}" for number in child["blocked_by"]) or "-"
        pending = f" pending_prs={','.join(child['pending_prs'])}" if child["pending_prs"] else ""
        final = " final_check" if child["final_check"] else ""
        print(f"- #{child['number']} {child['status']}{final} blocked_by={blockers}{pending} title={child['title']}")
    runnable = [child["number"] for child in plan["children"] if child["status"] == "runnable"]
    print("\nRunnable: " + (", ".join(f"#{number}" for number in runnable) or "-"))


def self_test() -> None:
    from render_issue_plan import tracker_body

    source_plan = {
        "tracker": {"title": "T", "goal": "G", "constraints": [], "non_goals": [], "definition_of_done": []},
        "issues": [
            {"id": "a", "title": "A", "purpose": "A.", "acceptance": ["A."], "testing": {"seam": "API", "validation": "python test.py", "do_not_test": "internals"}, "blocked_by": [], "blocks": ["b"], "parallelism": "First."},
            {"id": "b", "title": "B", "role": "final_check", "purpose": "B.", "acceptance": ["B."], "testing": {"seam": "integration", "validation": "python test.py", "do_not_test": "internals"}, "blocked_by": ["a"], "blocks": [], "parallelism": "Last."},
        ],
        "waves": [{"name": "First", "items": ["a"]}, {"name": "Last", "items": ["b"]}],
    }
    parent_body = tracker_body(source_plan, {"tracker": "#10", "a": "#11", "b": "#12"})
    graph = decode_embedded(parent_body)
    child_a = child_from_issue(
        {"number": 11, "title": "foundation", "state": "OPEN", "url": ""},
        graph["issues"][0],
    )
    child_b = child_from_issue(
        {
            "number": 12,
            "title": "final verification",
            "state": "OPEN",
            "url": "",
        },
        graph["issues"][1],
    )
    child_c = child_from_issue(
        {
            "number": 13,
            "title": "started work",
            "state": "OPEN",
            "url": "",
            "closedByPullRequestsReferences": [{"number": 3, "url": "https://github.com/org/repo/pull/3", "state": "OPEN"}],
        },
        {"blocked_by": [], "blocks": [], "role": "implementation"},
    )
    assert graph["tracker"] == 10
    for body, expected in (
        ("", "missing issue-plan-graph"),
        ("<!-- issue-plan-graph\n{bad}\n-->", "malformed issue-plan-graph"),
        ('<!-- issue-plan-graph\n{"version":2}\n-->', "unsupported issue-plan-graph version"),
        ('<!-- issue-plan-graph\n{"version":1,"tracker":10,"issues":{}}\n-->', "issues must be a non-empty list"),
    ):
        try:
            decode_embedded(body)
        except SystemExit as error:
            assert expected in str(error)
        else:
            raise AssertionError(f"expected graph error containing {expected!r}")
    classified = classify([child_a, child_b], "main")
    assert classified[0]["status"] == "runnable"
    assert classified[1]["status"] == "blocked"
    assert classified[1]["final_check"]
    classified[0]["state"] = "CLOSED"
    assert classify(classified, "main")[1]["status"] == "runnable"
    classified[0]["state"] = "OPEN"
    assert classify(classified, "main", {"11"})[0]["status"] == "done-local"
    assert classify(classified, "main", {"11"})[1]["status"] == "runnable"
    assert branch_mode("main", "main") == "default_branch_blocked"
    assert branch_mode("feature", "main") == "integration"
    assert local_done_numbers(classified, "main", "default_branch_blocked", lambda number, branch: True) == set()
    assert local_done_numbers(classified, "integration", "integration", lambda number, branch: number == "11") == {"11"}
    assert classify([child_c], "main")[0]["status"] == "pending-pr"
    assert graph_errors(classified) == []
    with tempfile.TemporaryDirectory() as tmp:
        old_cwd = os.getcwd()
        try:
            os.chdir(tmp)
            run(["git", "init", "-q", "-b", "integration"])
            Path("README.md").write_text("test\n", encoding="utf-8")
            run(["git", "add", "README.md"])
            run(["git", "-c", "user.name=Agent", "-c", "user.email=agent@example.invalid", "commit", "-qm", "init"])
            run(["git", "branch", "issue-11-child-slice"])
            assert local_branch_merged("11", "integration")
            assert not local_branch_merged("1", "integration")
        finally:
            os.chdir(old_cwd)


def main() -> int:
    parser = argparse.ArgumentParser(description="Inspect a dependency-aware shipyard parent issue.")
    parser.add_argument("parent_issue", nargs="?")
    parser.add_argument("--repo", help="OWNER/REPO; defaults to current repository")
    parser.add_argument("--json", action="store_true", help="Emit JSON")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()

    if args.self_test:
        self_test()
        return 0
    if not args.parent_issue:
        parser.error("parent_issue is required unless --self-test is used")

    try:
        GITHUB.authenticate()
        plan = inspect(args.parent_issue, args.repo)
    except (GitHubError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    errors = graph_errors(plan["children"])
    if errors:
        for error in errors:
            print(f"error: {error}", file=sys.stderr)
        return 1
    if args.json:
        print(json.dumps(plan, indent=2, sort_keys=True))
    else:
        print_text(plan)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
