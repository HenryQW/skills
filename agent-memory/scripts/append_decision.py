#!/usr/bin/env python3
"""Append durable decision or guidance candidates to local memory state."""

from __future__ import annotations

import argparse
import hashlib
import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from obsidian_project import topic_slug


DEFAULT_SOURCE = ".context/decisions.jsonl"


def append_candidate(
    project_root: Path,
    topic: str,
    source: str,
    files: list[str],
    durable: bool,
    *,
    decision: str = "",
    reason: str = "",
    alternatives: str = "",
    impact: str = "",
    guidance: str = "",
    applies_when: str = "",
    change: str = "",
    improvement: str = "",
    attention: str = "",
    output: str = DEFAULT_SOURCE,
) -> tuple[Path, bool]:
    path = project_root / output
    path.parent.mkdir(parents=True, exist_ok=True)
    if bool(decision.strip()) == bool(guidance.strip()):
        raise SystemExit("exactly one decision or guidance value is required")
    kind = "guidance" if guidance.strip() else "decision"
    values = {"topic": topic.strip(), "source": source.strip()}
    if kind == "decision":
        values.update(
            decision=decision.strip(),
            reason=reason.strip(),
            alternatives=alternatives.strip(),
            impact=impact.strip(),
        )
    else:
        values.update(
            guidance=guidance.strip(),
            applies_when=applies_when.strip(),
            change=change.strip(),
            improvement=improvement.strip(),
            attention=attention.strip(),
        )
    missing = [key for key, value in values.items() if not value]
    if missing:
        raise SystemExit(f"missing required {kind} fields: {', '.join(missing)}")
    record = {
        "type": kind,
        "topic": topic_slug(values["topic"]),
        "source": values["source"],
        "files": sorted(set(files)),
        "durable": durable,
        "created_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    }
    record.update({key: value for key, value in values.items() if key not in {"topic", "source"}})
    record["id"] = candidate_id(record["topic"], kind, record[kind])
    if record["id"] in existing_candidate_ids(path):
        return path, False
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, sort_keys=True, ensure_ascii=False) + "\n")
    return path, True


def candidate_id(topic: str, kind: str, value: str) -> str:
    payload = json.dumps(
        {
            kind: " ".join(value.split()).casefold(),
            "topic": topic_slug(topic),
            "type": kind,
        },
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(payload.encode()).hexdigest()


def existing_candidate_ids(path: Path) -> set[str]:
    if not path.exists():
        return set()
    ids: set[str] = set()
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError as exc:
            raise SystemExit(f"{path}:{number}: invalid JSON: {exc}") from exc
        kind = row.get("type", "decision")
        if kind in {"decision", "guidance"} and row.get("topic") and row.get(kind):
            ids.add(candidate_id(row["topic"], kind, row[kind]))
    return ids


def self_test() -> None:
    with tempfile.TemporaryDirectory() as raw:
        root = Path(raw)
        path, appended = append_candidate(
            root,
            topic="issue-workbench",
            source="self-test",
            files=["issue-workbench/SKILL.md"],
            durable=True,
            decision="Use lite mode for one actionable issue.",
            reason="Avoid parent graph overhead.",
            alternatives="A parent graph adds coordination without value for one issue.",
            impact="Single-issue work starts with fewer orchestration steps.",
        )
        _, duplicate = append_candidate(
            root,
            topic="Issue Workbench",
            source="self-test-2",
            files=[],
            durable=True,
            decision="  USE lite mode for one actionable issue. ",
            reason="Different wording does not create a duplicate.",
            alternatives="Not relevant to duplicate detection.",
            impact="Not relevant to duplicate detection.",
        )
        _, guidance_appended = append_candidate(
            root,
            topic="Review Checkpoint",
            source="self-test",
            files=[],
            durable=True,
            guidance="Treat stale summary prose as non-actionable.",
            applies_when="A review summary conflicts with the current diff and comments.",
            change="Review now compares summaries with live evidence before editing.",
            improvement="Prevents stale prose from reversing approved repository decisions.",
            attention="Future sessions must re-check the live diff and unresolved comments.",
        )
        _, guidance_duplicate = append_candidate(
            root,
            topic="review-checkpoint",
            source="self-test-2",
            files=[],
            durable=True,
            guidance="  TREAT stale summary prose as non-actionable. ",
            applies_when="Duplicate applicability does not matter.",
            change="Duplicate change.",
            improvement="Duplicate improvement.",
            attention="Duplicate attention.",
        )
        rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
        assert appended is True
        assert duplicate is False
        assert guidance_appended is True
        assert guidance_duplicate is False
        assert len(rows) == 2
        assert rows[0]["topic"] == "issue-workbench"
        assert rows[0]["durable"] is True
        assert rows[0]["files"] == ["issue-workbench/SKILL.md"]
        assert rows[0]["id"] == candidate_id(rows[0]["topic"], "decision", rows[0]["decision"])
        assert rows[1]["type"] == "guidance"
        assert rows[1]["applies_when"].startswith("A review summary")
        assert rows[1]["id"] == candidate_id(rows[1]["topic"], "guidance", rows[1]["guidance"])

        try:
            append_candidate(
                root,
                topic="incomplete-guidance",
                source="self-test",
                files=[],
                durable=True,
                guidance="Keep the shared boundary.",
            )
        except SystemExit as exc:
            assert "applies_when, change, improvement, attention" in str(exc)
        else:
            raise AssertionError("accepted incomplete guidance")

        rows[0]["id"] = rows[1]["id"] = "stale-id"
        path.write_text("\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8")
        _, stale_id_duplicate = append_candidate(
            root,
            topic="issue-workbench",
            source="self-test-3",
            files=[],
            durable=True,
            decision="Use lite mode for one actionable issue.",
            reason="Stored IDs are not trusted.",
            alternatives="Stored IDs could be trusted but may be stale.",
            impact="Duplicate detection remains deterministic.",
        )
        assert stale_id_duplicate is False
        assert len(path.read_text(encoding="utf-8").splitlines()) == 2


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", default=".")
    parser.add_argument("--topic")
    parser.add_argument("--decision")
    parser.add_argument("--reason")
    parser.add_argument("--alternatives")
    parser.add_argument("--impact")
    parser.add_argument("--guidance")
    parser.add_argument("--applies-when")
    parser.add_argument("--change")
    parser.add_argument("--improvement")
    parser.add_argument("--attention")
    parser.add_argument("--source")
    parser.add_argument("--file", action="append", default=[], dest="files")
    parser.add_argument("--output", default=DEFAULT_SOURCE)
    parser.add_argument("--non-durable", action="store_true")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return
    if bool(args.decision) == bool(args.guidance):
        parser.error("exactly one of --decision or --guidance is required")
    required = (
        ("topic", "source", "reason", "alternatives", "impact")
        if args.decision
        else ("topic", "source", "applies_when", "change", "improvement", "attention")
    )
    for field in required:
        if not getattr(args, field):
            parser.error(f"--{field} is required")
    path, appended = append_candidate(
        Path(args.project_root).resolve(),
        args.topic,
        args.source,
        args.files,
        not args.non_durable,
        decision=args.decision or "",
        reason=args.reason or "",
        alternatives=args.alternatives or "",
        impact=args.impact or "",
        guidance=args.guidance or "",
        applies_when=args.applies_when or "",
        change=args.change or "",
        improvement=args.improvement or "",
        attention=args.attention or "",
        output=args.output,
    )
    status = "APPENDED" if appended else "SKIPPED reason=duplicate"
    print(f"candidate_write={status} type={'decision' if args.decision else 'guidance'} path={args.output}")


if __name__ == "__main__":
    main()
