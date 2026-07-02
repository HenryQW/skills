#!/usr/bin/env python3
"""Compact Greptile JSON without assuming a fixed schema."""

from __future__ import annotations

import argparse
import json
import sys


FIELD_NAMES = {
    "file",
    "filepath",
    "path",
    "line",
    "startLine",
    "endLine",
    "severity",
    "title",
    "message",
    "body",
    "description",
}

NESTED_LOCATION_NAMES = {"location", "position", "range"}


def clip(value: object, limit: int) -> str:
    text = str(value).strip()
    return text if len(text) <= limit else text[: limit - 3].rstrip() + "..."


def flatten(value: dict[str, object]) -> dict[str, object]:
    picked = {key: value[key] for key in value if key in FIELD_NAMES and value[key] not in (None, "")}
    for nested_name in NESTED_LOCATION_NAMES:
        nested = value.get(nested_name)
        if isinstance(nested, dict):
            for key in FIELD_NAMES:
                if key in nested and key not in picked and nested[key] not in (None, ""):
                    picked[key] = nested[key]
    return picked


def walk(value: object) -> list[dict[str, object]]:
    findings: list[dict[str, object]] = []
    if isinstance(value, str):
        text = value.strip()
        if text.startswith(("{", "[")):
            try:
                findings.extend(walk(json.loads(text)))
            except json.JSONDecodeError:
                pass
    elif isinstance(value, list):
        for item in value:
            findings.extend(walk(item))
    elif isinstance(value, dict):
        picked = flatten(value)
        has_location = any(key in picked for key in ("file", "filepath", "path"))
        has_message = any(key in picked for key in ("title", "message", "body", "description"))
        is_finding = has_message and (has_location or any(key in value for key in ("severity", "rule", "check")))
        if is_finding:
            findings.append(picked)
        for key, item in value.items():
            if is_finding and key in NESTED_LOCATION_NAMES:
                continue
            findings.extend(walk(item))
    return findings


def main() -> int:
    parser = argparse.ArgumentParser(description="Compact Greptile JSON from stdin.")
    parser.add_argument("--limit", type=int, default=1200, help="Maximum characters per text field")
    args = parser.parse_args()

    raw = sys.stdin.read().strip()
    if not raw:
        return 0

    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        print(raw[: args.limit])
        return 2

    findings = walk(data)
    if not findings:
        print(json.dumps(data, separators=(",", ":"))[: args.limit])
        return 0

    for index, finding in enumerate(findings, 1):
        print(f"## Finding {index}")
        for key, value in finding.items():
            print(f"- {key}: {clip(value, args.limit)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
