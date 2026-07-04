#!/usr/bin/env python3
"""Inspect a shipyard parent issue and print a compact execution plan."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from typing import Any


SECTION_RE = re.compile(r"^##\s+(.+?)\s*$", re.MULTILINE)
ISSUE_REF_RE = re.compile(r"(?:https://github\.com/[^/\s]+/[^/\s]+/issues/|#)([1-9][0-9]*)")


def run(command: list[str]) -> str:
    return subprocess.check_output(command, text=True).strip()


def gh_json(args: list[str]) -> dict[str, Any]:
    return json.loads(run(["gh", *args]))


def issue_number(value: str) -> str:
    if re.fullmatch(r"[1-9][0-9]*", value):
        return value
    match = ISSUE_REF_RE.search(value)
    if not match:
        raise SystemExit(f"could not parse issue number: {value}")
    return match.group(1)


def section(text: str, title: str) -> str:
    matches = list(SECTION_RE.finditer(text or ""))
    for index, match in enumerate(matches):
        if match.group(1).strip().lower() != title.lower():
            continue
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        return text[start:end].strip()
    return ""


def refs(text: str) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for match in ISSUE_REF_RE.finditer(text or ""):
        number = match.group(1)
        if number not in seen:
            seen.add(number)
            result.append(number)
    return result


def child_from_issue(issue: dict[str, Any]) -> dict[str, Any]:
    body = issue.get("body") or ""
    labels = {label.get("name", "").lower() for label in issue.get("labels") or []}
    title = issue.get("title", "")
    return {
        "number": str(issue["number"]),
        "title": title,
        "state": issue.get("state", ""),
        "url": issue.get("url", ""),
        "blocked_by": refs(section(body, "Blocked by")),
        "blocks": refs(section(body, "Blocks")),
        "parallelism": section(body, "Parallelism"),
        "final_check": "final_check" in labels or "final_check" in body or "final_check" in title.lower(),
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


def mark_final_check(children: list[dict[str, Any]]) -> None:
    child_numbers = {child["number"] for child in children}
    for child in children:
        graph_final = not child["blocks"] and set(child["blocked_by"]) == child_numbers - {child["number"]}
        child["final_check"] = child["final_check"] or graph_final


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


def classify(children: list[dict[str, Any]], default_branch: str) -> list[dict[str, Any]]:
    mark_final_check(children)
    by_number = {child["number"]: child for child in children}
    for child in children:
        blockers = [by_number.get(number) for number in child["blocked_by"]]
        missing = [number for number, blocker in zip(child["blocked_by"], blockers) if blocker is None]
        open_blockers = [blocker["number"] for blocker in blockers if blocker and not child_is_done(blocker, default_branch)]
        pending_pr = has_pending_pr(child, default_branch)
        if child_is_done(child, default_branch):
            status = "done"
        elif pending_pr:
            status = "pending-pr"
        elif missing:
            status = "blocked-missing"
        elif open_blockers:
            status = "blocked"
        elif child["final_check"] and any(
            other["number"] != child["number"] and not child_is_done(other, default_branch) for other in children
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
    parent_number = issue_number(parent_issue)
    repo_args = ["--repo", repo] if repo else []
    parent = gh_json(["issue", "view", parent_number, *repo_args, "--json", "number,title,url,body,state"])
    child_numbers = [number for number in refs(parent.get("body") or "") if number != str(parent["number"])]
    children = [
        child_from_issue(
            gh_json(
                [
                    "issue",
                    "view",
                    number,
                    *repo_args,
                    "--json",
                    "number,title,url,state,body,labels,closedByPullRequestsReferences",
                ]
            )
        )
        for number in child_numbers
    ]
    default_branch = gh_json(["repo", "view", *repo_args, "--json", "defaultBranchRef"])["defaultBranchRef"]["name"]
    current_branch = run(["git", "branch", "--show-current"])
    if not current_branch:
        raise SystemExit("detached HEAD is not supported")
    return {
        "parent": {
            "number": str(parent["number"]),
            "title": parent.get("title", ""),
            "state": parent.get("state", ""),
            "url": parent.get("url", ""),
        },
        "default_branch": default_branch,
        "current_branch": current_branch,
        "mode": "child_pr" if current_branch == default_branch else "integration",
        "children": classify(children, default_branch),
    }


def print_text(plan: dict[str, Any]) -> None:
    parent = plan["parent"]
    print(f"Parent: #{parent['number']} {parent['title']}")
    print(f"URL: {parent['url']}")
    print(f"Mode: {plan['mode']} ({plan['current_branch']} vs {plan['default_branch']})")
    print("\nChildren:")
    for child in plan["children"]:
        blockers = ", ".join(f"#{number}" for number in child["blocked_by"]) or "-"
        pending = f" pending_prs={','.join(child['pending_prs'])}" if child["pending_prs"] else ""
        final = " final_check" if child["final_check"] else ""
        print(f"- #{child['number']} {child['status']}{final} blocked_by={blockers}{pending} title={child['title']}")
    runnable = [child["number"] for child in plan["children"] if child["status"] == "runnable"]
    print("\nRunnable: " + (", ".join(f"#{number}" for number in runnable) or "-"))


def self_test() -> None:
    parent_body = "| #11 | work | - | #12 |\n| #12 | final | #11 | - |"
    child_a = child_from_issue(
        {"number": 11, "title": "foundation", "state": "OPEN", "url": "", "labels": [], "body": "## Blocked by\n-\n## Blocks\n#12"}
    )
    child_b = child_from_issue(
        {
            "number": 12,
            "title": "final verification",
            "state": "OPEN",
            "url": "",
            "labels": [],
            "body": "## Blocked by\n#11\n## Blocks\n-",
        }
    )
    child_c = child_from_issue(
        {
            "number": 13,
            "title": "started work",
            "state": "OPEN",
            "url": "",
            "labels": [],
            "body": "## Blocked by\n-\n## Blocks\n-",
            "closedByPullRequestsReferences": [{"number": 3, "url": "https://github.com/org/repo/pull/3", "state": "OPEN"}],
        }
    )
    assert refs(parent_body) == ["11", "12"]
    assert section(child_b["parallelism"], "anything") == ""
    classified = classify([child_a, child_b], "main")
    assert classified[0]["status"] == "runnable"
    assert classified[1]["status"] == "blocked"
    assert classified[1]["final_check"]
    classified[0]["state"] = "CLOSED"
    assert classify(classified, "main")[1]["status"] == "runnable"
    assert classify([child_c], "main")[0]["status"] == "pending-pr"
    assert graph_errors(classified) == []


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

    plan = inspect(args.parent_issue, args.repo)
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
