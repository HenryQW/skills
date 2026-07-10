#!/usr/bin/env python3
"""Append durable decision candidates to .context/decisions.jsonl."""

from __future__ import annotations

import argparse
import hashlib
import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from obsidian_project import topic_slug


DEFAULT_SOURCE = ".context/decisions.jsonl"


def append_decision(
    project_root: Path,
    topic: str,
    decision: str,
    reason: str,
    source: str,
    files: list[str],
    durable: bool,
    output: str = DEFAULT_SOURCE,
) -> tuple[Path, bool]:
    path = project_root / output
    path.parent.mkdir(parents=True, exist_ok=True)
    values = {
        "topic": topic.strip(),
        "decision": decision.strip(),
        "reason": reason.strip(),
        "source": source.strip(),
    }
    missing = [key for key, value in values.items() if not value]
    if missing:
        raise SystemExit(f"missing required decision fields: {', '.join(missing)}")
    record = {
        "type": "decision",
        "topic": topic_slug(values["topic"]),
        "decision": values["decision"],
        "reason": values["reason"],
        "source": values["source"],
        "files": sorted(set(files)),
        "durable": durable,
        "created_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    }
    record["id"] = decision_id(record["topic"], record["decision"])
    if record["id"] in existing_decision_ids(path):
        return path, False
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, sort_keys=True, ensure_ascii=False) + "\n")
    return path, True


def decision_id(topic: str, decision: str) -> str:
    payload = json.dumps(
        {
            "decision": " ".join(decision.split()).casefold(),
            "topic": topic_slug(topic),
            "type": "decision",
        },
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(payload.encode()).hexdigest()


def existing_decision_ids(path: Path) -> set[str]:
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
        if row.get("type", "decision") == "decision" and row.get("topic") and row.get("decision"):
            ids.add(decision_id(row["topic"], row["decision"]))
    return ids


def self_test() -> None:
    with tempfile.TemporaryDirectory() as raw:
        root = Path(raw)
        path, appended = append_decision(
            root,
            topic="issue-workbench",
            decision="Use lite mode for one actionable issue.",
            reason="Avoid parent graph overhead.",
            source="self-test",
            files=["issue-workbench/SKILL.md"],
            durable=True,
        )
        _, duplicate = append_decision(
            root,
            topic="Issue Workbench",
            decision="  USE lite mode for one actionable issue. ",
            reason="Different wording does not create a duplicate.",
            source="self-test-2",
            files=[],
            durable=True,
        )
        rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
        assert appended is True
        assert duplicate is False
        assert len(rows) == 1
        assert rows[0]["topic"] == "issue-workbench"
        assert rows[0]["durable"] is True
        assert rows[0]["files"] == ["issue-workbench/SKILL.md"]
        assert rows[0]["id"] == decision_id(rows[0]["topic"], rows[0]["decision"])

        rows[0]["id"] = "stale-id"
        path.write_text(json.dumps(rows[0]) + "\n", encoding="utf-8")
        _, stale_id_duplicate = append_decision(
            root,
            topic="issue-workbench",
            decision="Use lite mode for one actionable issue.",
            reason="Stored IDs are not trusted.",
            source="self-test-3",
            files=[],
            durable=True,
        )
        assert stale_id_duplicate is False
        assert len(path.read_text(encoding="utf-8").splitlines()) == 1


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", default=".")
    parser.add_argument("--topic")
    parser.add_argument("--decision")
    parser.add_argument("--reason")
    parser.add_argument("--source")
    parser.add_argument("--file", action="append", default=[], dest="files")
    parser.add_argument("--output", default=DEFAULT_SOURCE)
    parser.add_argument("--non-durable", action="store_true")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return
    for field in ("topic", "decision", "reason", "source"):
        if not getattr(args, field):
            parser.error(f"--{field} is required")
    path, appended = append_decision(
        Path(args.project_root).resolve(),
        args.topic,
        args.decision,
        args.reason,
        args.source,
        args.files,
        not args.non_durable,
        args.output,
    )
    status = "APPENDED" if appended else "SKIPPED reason=duplicate"
    print(f"decision_write={status} path={args.output}")


if __name__ == "__main__":
    main()
