#!/usr/bin/env python3
"""
Build normalized review-batch artifacts from gh-autopilot cycle artifacts.

Input:
  - .context/gh-autopilot/cycle.json
Output:
  - .context/gh-autopilot/review-batch.json
"""

from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

BATCH_VERSION = 1


def now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def render_json(data: dict[str, Any]) -> str:
    return json.dumps(data, indent=2, sort_keys=True)


def _require(payload: dict[str, Any], key: str) -> Any:
    if key not in payload:
        raise ValueError(f"cycle payload is missing required key: {key}")
    return payload[key]


def _first_line(text: str, *, default: str = "(empty)") -> str:
    stripped = (text or "").strip()
    if not stripped:
        return default
    return stripped.splitlines()[0]


def validate_cycle_payload(cycle_payload: dict[str, Any]) -> None:
    _require(cycle_payload, "status")
    _require(cycle_payload, "cycle")
    _require(cycle_payload, "pull_request")
    _require(cycle_payload, "copilot_review")
    _require(cycle_payload, "copilot_threads")


def _latest_comment(comments: list[dict[str, Any]]) -> dict[str, Any] | None:
    if not comments:
        return None
    return max(comments, key=lambda item: (item.get("created_at") or "", item.get("id") or ""))


def build_review_batch(cycle_payload: dict[str, Any], *, cycle_path: Path) -> dict[str, Any]:
    validate_cycle_payload(cycle_payload)

    threads = cycle_payload.get("copilot_threads") or []
    normalized_threads: list[dict[str, Any]] = []
    eligible_count = 0

    for idx, thread in enumerate(threads, start=1):
        comments = thread.get("comments") or []
        latest = _latest_comment(comments)
        eligible = bool(thread.get("eligible_for_addressing"))
        if eligible:
            eligible_count += 1

        normalized_threads.append(
            {
                "index": idx,
                "thread_id": thread.get("thread_id"),
                "thread_number": thread.get("thread_number"),
                "path": thread.get("path"),
                "line": thread.get("line"),
                "eligible_for_addressing": eligible,
                "comment_count": len(comments),
                "latest_comment": latest,
                "comments": comments,
                "classification": "pending",
                "resolution": {
                    "status": "pending",
                    "rationale": None,
                    "actions": [],
                },
            }
        )

    return {
        "version": BATCH_VERSION,
        "generated_at": now_iso(),
        "source": {
            "cycle_json": str(cycle_path.resolve()),
            "cycle_status": cycle_payload.get("status"),
        },
        "pull_request": cycle_payload.get("pull_request"),
        "cycle": cycle_payload.get("cycle"),
        "copilot_review": cycle_payload.get("copilot_review"),
        "summary": {
            "threads_total": len(normalized_threads),
            "threads_eligible": eligible_count,
            "threads_pending": len(normalized_threads),
        },
        "threads": normalized_threads,
    }


def render_review_batch_markdown(batch: dict[str, Any]) -> str:
    lines: list[str] = []
    pr = batch["pull_request"]
    review = batch["copilot_review"]
    summary = batch["summary"]

    lines.append("# GH Autopilot Review Batch")
    lines.append("")
    lines.append(f"- Generated: {batch['generated_at']}")
    lines.append(f"- Cycle: {batch['cycle']}")
    lines.append(f"- PR: #{pr.get('number')} ({pr.get('url')})")
    lines.append(f"- Review id: {review.get('id')}")
    lines.append(
        f"- Threads: total={summary['threads_total']} eligible={summary['threads_eligible']} pending={summary['threads_pending']}"
    )
    lines.append("")
    lines.append("## Thread Queue")
    lines.append("")

    threads = batch.get("threads") or []
    if not threads:
        lines.append("- No Copilot threads found in cycle artifact.")
        lines.append("")
        return "\n".join(lines)

    for thread in threads:
        latest = thread.get("latest_comment") or {}
        comment_body = _first_line(latest.get("body", ""))
        lines.append(
            f"- [{thread['index']}] id={thread.get('thread_id')} "
            f"path={thread.get('path')} line={thread.get('line')} "
            f"eligible={thread.get('eligible_for_addressing')} "
            f"classification={thread.get('classification')}"
        )
        lines.append(f"  latest: {comment_body}")
    lines.append("")
    lines.append("Valid classifications: actionable | non-actionable | needs-clarification")
    lines.append("")
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build normalized review-batch artifacts from gh-autopilot cycle data."
    )
    parser.add_argument(
        "--cycle",
        default=".context/gh-autopilot/cycle.json",
        help="Path to cycle.json generated by gh-autopilot.",
    )
    parser.add_argument(
        "--output-dir",
        default=".context/gh-autopilot",
        help="Output directory for review-batch artifacts.",
    )
    parser.add_argument(
        "--batch-json",
        default=None,
        help="Override review-batch.json output path.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    cycle_path = Path(args.cycle).resolve()
    output_dir = Path(args.output_dir).resolve()
    batch_json = Path(args.batch_json).resolve() if args.batch_json else output_dir / "review-batch.json"

    if not cycle_path.exists():
        raise FileNotFoundError(f"cycle file not found: {cycle_path}")

    payload = json.loads(cycle_path.read_text(encoding="utf-8"))
    batch = build_review_batch(payload, cycle_path=cycle_path)

    batch_json.parent.mkdir(parents=True, exist_ok=True)
    batch_json.write_text(render_json(batch) + "\n", encoding="utf-8")

    print(
        render_json(
            {
                "status": "ok",
                "review_batch_json": str(batch_json),
                "threads_total": batch["summary"]["threads_total"],
                "threads_eligible": batch["summary"]["threads_eligible"],
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
