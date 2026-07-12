#!/usr/bin/env python3
"""Render a dependency-aware GitHub issue plan from JSON."""

from __future__ import annotations

import argparse
import json
import re
import tempfile
from pathlib import Path

from issue_graph_contract import embed, graph_payload
from issue_plan import final_check, load_plan, ordered_issues, validate


def slug(text: str) -> str:
    return re.sub(r"[^a-z0-9-]+", "-", text.lower()).strip("-")


def refs(ids: list[str], numbers: dict[str, str]) -> str:
    return ", ".join(numbers.get(item, f"`{item}`") for item in ids) or "None."


def checkbox(items: list[str]) -> str:
    return "\n".join(f"- [ ] {item}" for item in items) or "- [ ] Define acceptance criteria."


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


def child_body(plan: dict, issue: dict, numbers: dict[str, str], tracker_issue: str | None) -> str:
    context = "\n".join(f"- {line}" for line in issue.get("context", [])) or "- No extra context."
    execution = "\n\n## Execution\n\nVerification only. Do not edit code; return implementation defects to the owning child issue." if issue.get("role") == "final_check" else ""
    return f"""## Tracker

{tracker_issue or numbers.get("tracker", "Tracker issue pending.")}

## What to build

{issue["purpose"]}

Context:
{context}{execution}

## Acceptance criteria

{checkbox(issue.get("acceptance", []))}

## Testing

{testing_section(issue)}

## Blocked by

{refs(issue.get("blocked_by", []), numbers)}

## Blocks

{refs(issue.get("blocks", []), numbers)}

## Parallelism

{issue.get("parallelism", "No parallelism notes.")}{graph_section(plan, numbers)}
"""


def graph_section(plan: dict, numbers: dict[str, str]) -> str:
    required = {"tracker", *(issue["id"] for issue in plan["issues"])}
    return f"\n\n{embed(plan, numbers)}" if required <= set(numbers) else ""


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
    return "\n".join(lines) + graph_section(plan, numbers)


def render(plan_path: Path, out: Path, numbers_path: Path | None, tracker_issue: str | None) -> None:
    plan = load_plan(plan_path)
    numbers = json.loads(numbers_path.read_text()) if numbers_path else {}
    out.mkdir(parents=True, exist_ok=True)
    (out / "00-tracker.md").write_text(tracker_body(plan, numbers))
    rows = []
    for index, issue in enumerate(ordered_issues(plan), 1):
        file = out / f"{index:02d}-{slug(issue['id'])}.md"
        file.write_text(child_body(plan, issue, numbers, tracker_issue))
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
    assert [issue["id"] for issue in ordered_issues(plan)] == ["a", "b"]
    assert final_check(plan)["id"] == "b"
    assert graph_payload(plan, {"tracker": "#9", "a": "#1", "b": "#2"})["issues"][1]["role"] == "final_check"

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
    invalid = json.loads(json.dumps(plan))
    invalid["issues"][0]["testing"]["validation"] = "All checks pass."
    assert_invalid(invalid, "concrete integration commands")
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
        assert "issue-plan-graph" not in (out / "00-tracker.md").read_text()
        assert "duplicate cleanup" in (out / "00-tracker.md").read_text()
        assert "a\tA\t" in (out / "create-order.tsv").read_text()
        nums.write_text(json.dumps({"tracker": "#9", "a": "#1", "b": "#2"}))
        render(plan_path, out, nums, "#9")
        assert '"version":1' in (out / "00-tracker.md").read_text()
        assert '"role":"final_check"' in (out / "02-b.md").read_text()
        assert "Verification only. Do not edit code" in (out / "02-b.md").read_text()


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
