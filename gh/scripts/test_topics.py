#!/usr/bin/env python3
"""Focused checks for compact shared-topic references."""

from pathlib import Path
import sys


sys.path.insert(0, str(Path(__file__).parent))
from topics import EXPOSED_TOPICS, render_topic  # noqa: E402


ROOT = Path(__file__).resolve().parents[1] / "references" / "topic-sources"


def main() -> int:
    rendered = {
        path.stem: render_topic(path.stem, path.read_text())
        for path in ROOT.glob("*.txt")
    }
    assert {name for name, content in rendered.items() if content} == set(EXPOSED_TOPICS)
    assert rendered["actions"] is None
    assert rendered["telemetry"] is None
    assert "GH_TELEMETRY" in rendered["environment"]
    assert "GH_SPINNER_DISABLED" in rendered["environment"]
    assert "--json field1,field2" in rendered["formatting"]
    assert "`tablerow <fields>...`" in rendered["formatting"]
    assert "gh config set accessible_prompter enabled" in rendered["accessibility"]
    assert "| 4 |" in rendered["exit-codes"]
    assert "winpty" in rendered["mintty"]
    for content in rendered.values():
        if content:
            assert content.endswith("\n") and not content.endswith("\n\n")
            assert "https://" not in content
    print("gh topic tests ok: five compact topics, two redundant topics omitted")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
