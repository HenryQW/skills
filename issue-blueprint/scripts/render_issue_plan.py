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
    final_checks = [issue for issue in issues if issue.get("role") == "final_check"]
    if len(final_checks) != 1:
        raise SystemExit("exactly one issue must have role final_check")
    final_check = final_checks[0]
    final_id = final_check["id"]
    non_final = known - {final_id}
    if set(final_check.get("blocked_by", [])) != non_final:
        raise SystemExit(f"{final_id} must be blocked by every non-final issue")
    if final_check.get("blocks"):
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


def testing_section(issue: dict) -> str:
    testing = issue.get("testing") or {}
    seam = testing.get("seam", "Not specified.")
    existing = testing.get("existing_tests", "Not specified.")
    validation = testing.get("validation", "Not specified.")
    do_not_test = testing.get("do_not_test", "Implementation details.")
    return "\n".join(
        [
            f"- Seam: {seam}",
            f"- Existing similar tests: {existing}",
            f"- Validation command: {validation}",
            f"- Do not test: {do_not_test}",
        ]
    )


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

## Testing

{testing_section(issue)}

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
        "## Dropped findings",
        "",
    ]
    dropped = plan.get("dropped_findings", [])
    if dropped:
        lines += [f"- {item['finding']} - {item['reason']}" for item in dropped]
    else:
        lines.append("- None.")
    lines += [
        "",
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
    reference = Path(__file__).resolve().parents[1] / "references" / "issue-plan.md"
    example = re.search(r"```json[ \t]*\r?\n(.*?)\r?\n```", reference.read_text(), re.DOTALL)
    assert example is not None
    validate(json.loads(example.group(1)))

    plan = {
        "tracker": {"title": "x", "goal": "g", "constraints": ["c"], "non_goals": ["n"], "definition_of_done": ["d"]},
        "dropped_findings": [{"finding": "duplicate cleanup", "reason": "duplicate of #1"}],
        "issues": [
            {"id": "b", "title": "B", "role": "final_check", "purpose": "B work.", "acceptance": ["b ok"], "testing": {"seam": "final integration", "validation": "pytest", "do_not_test": "child-owned internals"}, "blocked_by": ["a"], "blocks": [], "parallelism": "Final tail."},
            {"id": "a", "title": "A", "purpose": "A work.", "acceptance": ["a ok"], "testing": {"seam": "public API", "existing_tests": "none found", "validation": "pytest tests/test_a.py", "do_not_test": "private helpers"}, "blocked_by": [], "blocks": ["b"], "parallelism": "Root work."},
        ],
        "waves": [
            {"name": "Wave 0", "items": ["a"], "notes": "start"},
            {"name": "Wave 1", "items": ["b"], "notes": "finish"},
        ],
    }

    def assert_invalid(candidate: dict, expected: str) -> None:
        try:
            validate(candidate)
        except SystemExit as error:
            assert expected in str(error)
        else:
            raise AssertionError(f"expected validation failure containing {expected!r}")

    for field in ("title", "purpose", "acceptance", "parallelism"):
        invalid = json.loads(json.dumps(plan))
        del invalid["issues"][1][field]
        assert_invalid(invalid, f"a.{field}")
    invalid = json.loads(json.dumps(plan))
    del invalid["waves"]
    assert_invalid(invalid, "waves must be a non-empty list")
    invalid = json.loads(json.dumps(plan))
    invalid["waves"].insert(1, {"name": "Duplicate", "items": ["a"]})
    assert_invalid(invalid, "repeats issue membership")
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        plan_path = root / "plan.json"
        nums = root / "numbers.json"
        out = root / "out"
        plan_path.write_text(json.dumps(plan))
        nums.write_text(json.dumps({"a": "#1", "b": "#2"}))
        render(plan_path, out, nums, "#9")
        assert "#9" in (out / "01-a.md").read_text()
        assert "## Testing" in (out / "01-a.md").read_text()
        assert "#1" in (out / "00-tracker.md").read_text()
        assert "duplicate cleanup" in (out / "00-tracker.md").read_text()
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
