#!/usr/bin/env python3
"""Render a dependency-aware GitHub issue plan from JSON."""

from __future__ import annotations

import argparse
import json
import re
import tempfile
from pathlib import Path

ID_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")


def slug(text: str) -> str:
    return re.sub(r"[^a-z0-9-]+", "-", text.lower()).strip("-")


def refs(ids: list[str], numbers: dict[str, str]) -> str:
    return ", ".join(numbers.get(item, f"`{item}`") for item in ids) or "None."


def checkbox(items: list[str]) -> str:
    return "\n".join(f"- [ ] {item}" for item in items) or "- [ ] Define acceptance criteria."


def validate(plan: dict) -> None:
    if not plan.get("tracker", {}).get("title"):
        raise SystemExit("tracker.title is required")
    ids = [item["id"] for item in plan["issues"]]
    if len(ids) != len(set(ids)):
        raise SystemExit("duplicate issue id")
    bad_ids = [item for item in ids if not ID_RE.match(item)]
    if bad_ids:
        raise SystemExit(f"invalid issue id: {bad_ids}")
    known = set(ids)
    by_id = {issue["id"]: issue for issue in plan["issues"]}
    final_checks = [issue for issue in plan["issues"] if issue.get("role") == "final_check"]
    if len(final_checks) != 1:
        raise SystemExit("exactly one issue must have role final_check")
    final_check = final_checks[0]
    final_id = final_check["id"]
    non_final = known - {final_id}
    if set(final_check.get("blocked_by", [])) != non_final:
        raise SystemExit(f"{final_id} must be blocked by every non-final issue")
    if final_check.get("blocks"):
        raise SystemExit(f"{final_id} final_check must not block other issues")
    for issue in plan["issues"]:
        issue_id = issue["id"]
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
    seen: set[str] = set()
    for wave in plan.get("waves", []):
        items = wave.get("items", [])
        missing = set(items) - known
        if missing:
            raise SystemExit(f"{wave['name']} has unknown items: {sorted(missing)}")
        for item in items:
            blockers = set(by_id[item].get("blocked_by", []))
            if not blockers <= seen:
                raise SystemExit(f"{wave['name']} schedules {item} before blockers {sorted(blockers - seen)}")
        seen.update(items)
    if plan.get("waves") and seen != known:
        raise SystemExit(f"waves omit issues: {sorted(known - seen)}")


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


def child_body(issue: dict, numbers: dict[str, str], tracker_issue: str | None) -> str:
    context = "\n".join(f"- {line}" for line in issue.get("context", [])) or "- No extra context."
    return f"""## Tracker

{tracker_issue or numbers.get("tracker", "Tracker issue pending.")}

## What to build

{issue["purpose"]}

Context:
{context}

## Acceptance criteria

{checkbox(issue.get("acceptance", []))}

## Blocked by

{refs(issue.get("blocked_by", []), numbers)}

## Blocks

{refs(issue.get("blocks", []), numbers)}

## Parallelism

{issue.get("parallelism", "No parallelism notes.")}
"""


def tracker_body(plan: dict, numbers: dict[str, str]) -> str:
    tracker = plan["tracker"]
    lines = [
        "## Goal",
        "",
        tracker["goal"],
        "",
        "## Constraints",
        "",
        *[f"- {item}" for item in tracker.get("constraints", [])],
        "",
        "## Issue graph",
        "",
        "| Issue | Purpose | Blocked by | Blocks |",
        "| --- | --- | --- | --- |",
    ]
    for issue in ordered_issues(plan):
        issue_ref = numbers.get(issue["id"], f"`{issue['id']}`")
        lines.append(
            f"| {issue_ref} | {issue['purpose']} | "
            f"{refs(issue.get('blocked_by', []), numbers)} | {refs(issue.get('blocks', []), numbers)} |"
        )
    lines += ["", "## Parallel implementation plan", ""]
    for wave in plan.get("waves", []):
        lines += [f"{wave['name']}:", f"- {refs(wave.get('items', []), numbers)}"]
        if wave.get("notes"):
            lines.append(f"- {wave['notes']}")
        lines.append("")
    lines += [
        "## Non-goals",
        "",
        *[f"- {item}" for item in tracker.get("non_goals", [])],
        "",
        "## Definition of done",
        "",
        *[f"- [ ] {item}" for item in tracker.get("definition_of_done", [])],
        "",
    ]
    return "\n".join(lines)


def render(plan_path: Path, out: Path, numbers_path: Path | None, tracker_issue: str | None) -> None:
    plan = json.loads(plan_path.read_text())
    validate(plan)
    numbers = json.loads(numbers_path.read_text()) if numbers_path else {}
    out.mkdir(parents=True, exist_ok=True)
    (out / "00-tracker.md").write_text(tracker_body(plan, numbers))
    rows = []
    for index, issue in enumerate(ordered_issues(plan), 1):
        file = out / f"{index:02d}-{slug(issue['id'])}.md"
        file.write_text(child_body(issue, numbers, tracker_issue))
        rows.append(f"{issue['id']}\t{issue['title']}\t{file}")
    (out / "create-order.tsv").write_text("\n".join(rows) + "\n")


def self_test() -> None:
    plan = {
        "tracker": {"title": "x", "goal": "g", "constraints": ["c"], "non_goals": ["n"], "definition_of_done": ["d"]},
        "issues": [
            {"id": "b", "title": "B", "role": "final_check", "purpose": "B work.", "acceptance": ["b ok"], "blocked_by": ["a"], "blocks": []},
            {"id": "a", "title": "A", "purpose": "A work.", "acceptance": ["a ok"], "blocked_by": [], "blocks": ["b"]},
        ],
        "waves": [
            {"name": "Wave 0", "items": ["a"], "notes": "start"},
            {"name": "Wave 1", "items": ["b"], "notes": "finish"},
        ],
    }
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        plan_path = root / "plan.json"
        nums = root / "numbers.json"
        out = root / "out"
        plan_path.write_text(json.dumps(plan))
        nums.write_text(json.dumps({"a": "#1", "b": "#2"}))
        render(plan_path, out, nums, "#9")
        assert "#9" in (out / "01-a.md").read_text()
        assert "#1" in (out / "00-tracker.md").read_text()
        assert "a\tA\t" in (out / "create-order.tsv").read_text()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("plan", nargs="?")
    parser.add_argument("--out", default=".context/issues")
    parser.add_argument("--numbers")
    parser.add_argument("--tracker")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return
    if not args.plan:
        raise SystemExit("plan JSON path required")
    render(Path(args.plan), Path(args.out), Path(args.numbers) if args.numbers else None, args.tracker)


if __name__ == "__main__":
    main()
