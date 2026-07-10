#!/usr/bin/env python3
"""Append durable decision candidates to .context/decisions.jsonl."""

from __future__ import annotations

import argparse
import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path


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
) -> Path:
    path = project_root / output
    path.parent.mkdir(parents=True, exist_ok=True)
    record = {
        "type": "decision",
        "topic": topic.strip(),
        "decision": decision.strip(),
        "reason": reason.strip(),
        "source": source.strip(),
        "files": files,
        "durable": durable,
        "created_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    }
    missing = [key for key in ("topic", "decision", "reason", "source") if not record[key]]
    if missing:
        raise SystemExit(f"missing required decision fields: {', '.join(missing)}")
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, sort_keys=True, ensure_ascii=False) + "\n")
    return path


def self_test() -> None:
    with tempfile.TemporaryDirectory() as raw:
        root = Path(raw)
        path = append_decision(
            root,
            topic="issue-workbench",
            decision="Use lite mode for one actionable issue.",
            reason="Avoid parent graph overhead.",
            source="self-test",
            files=["issue-workbench/SKILL.md"],
            durable=True,
        )
        rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
        assert len(rows) == 1
        assert rows[0]["topic"] == "issue-workbench"
        assert rows[0]["durable"] is True
        assert rows[0]["files"] == ["issue-workbench/SKILL.md"]


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
    path = append_decision(
        Path(args.project_root).resolve(),
        args.topic,
        args.decision,
        args.reason,
        args.source,
        args.files,
        not args.non_durable,
        args.output,
    )
    print(f"decision_appended={path}")


if __name__ == "__main__":
    main()
