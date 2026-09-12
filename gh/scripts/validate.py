#!/usr/bin/env python3
"""Validate the generated GitHub CLI manual inventory."""

from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[1]
REFERENCES = ROOT / "references"


def recorded_count(label: str, snapshot: str) -> int:
    match = re.search(rf"^{re.escape(label)}: (\d+)$", snapshot, re.MULTILINE)
    if not match:
        raise ValueError(f"snapshot missing {label} count")
    return int(match.group(1))


def main() -> int:
    snapshot = (REFERENCES / "snapshot.txt").read_text()
    commands = list((REFERENCES / "commands").rglob("README.md"))
    topics = list((REFERENCES / "topics").glob("*.md"))

    if len(commands) != recorded_count("commands", snapshot):
        raise ValueError("command count does not match snapshot")
    if len(topics) != recorded_count("help topics", snapshot):
        raise ValueError("help-topic count does not match snapshot")
    for path in commands:
        text = path.read_text()
        if "\nUSAGE\n" not in text and "\nUsage:\n" not in text:
            raise ValueError(f"missing usage section: {path.relative_to(ROOT)}")

    print(f"gh manual ok: {len(commands)} commands, {len(topics)} help topics")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
