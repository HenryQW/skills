#!/usr/bin/env python3
"""Validate the generated, progressively loadable GitHub CLI manual."""

from pathlib import Path
import re
import sys


sys.path.insert(0, str(Path(__file__).parent))
from compact import FACETS, render_help  # noqa: E402


ROOT = Path(__file__).resolve().parents[1]
REFERENCES = ROOT / "references"
COMMANDS = REFERENCES / "commands"
TOPICS = REFERENCES / "topics"


def recorded_count(label: str, snapshot: str) -> int:
    match = re.search(rf"^{re.escape(label)}: (\d+)$", snapshot, re.MULTILINE)
    if not match:
        raise ValueError(f"snapshot missing {label} count")
    return int(match.group(1))


def command_path(help_path: Path) -> tuple[str, ...]:
    relative = help_path.parent.relative_to(COMMANDS)
    return () if relative == Path(".") else relative.parts


def assert_clean(path: Path, content: str) -> None:
    if not content.endswith("\n") or content.endswith("\n\n"):
        raise ValueError(f"invalid terminal newline: {path.relative_to(ROOT)}")
    if any(line != line.rstrip() for line in content.splitlines()):
        raise ValueError(f"trailing whitespace: {path.relative_to(ROOT)}")


def main() -> int:
    snapshot = (REFERENCES / "snapshot.txt").read_text()
    help_files = sorted(COMMANDS.rglob("help.txt"))
    topic_files = sorted(TOPICS.glob("*.md"))
    manifest = (REFERENCES / "manifest.txt").read_text().splitlines()

    command_count = recorded_count("commands", snapshot)
    topic_count = recorded_count("help topics", snapshot)
    if len(help_files) != command_count or len(manifest) != command_count:
        raise ValueError("command inventory does not match snapshot")
    if len(topic_files) != topic_count or list(TOPICS.glob("*.txt")):
        raise ValueError("help-topic inventory does not match snapshot")

    expected_manifest = ["/".join(command_path(path)) or "." for path in help_files]
    if sorted(manifest) != sorted(expected_manifest):
        raise ValueError("manifest does not match command directories")

    readme_bytes = 0
    help_bytes = 0
    for help_path in help_files:
        raw = help_path.read_text()
        expected = render_help(raw, command_path(help_path))
        directory = help_path.parent
        actual_names = {name for name in FACETS if (directory / name).is_file()}
        if actual_names != set(expected):
            raise ValueError(f"facet inventory drift: {directory.relative_to(ROOT)}")
        for name, expected_content in expected.items():
            target = directory / name
            actual = target.read_text()
            if actual != expected_content:
                raise ValueError(f"generated facet drift: {target.relative_to(ROOT)}")
            assert_clean(target, actual)

        readme = directory / "README.md"
        if readme.stat().st_size >= help_path.stat().st_size:
            raise ValueError(f"README is not smaller than help.txt: {directory.relative_to(ROOT)}")
        readme_bytes += readme.stat().st_size
        help_bytes += help_path.stat().st_size

    ratio = readme_bytes / help_bytes
    if ratio > 0.35:
        raise ValueError(f"aggregate README/help ratio exceeds 35%: {ratio:.1%}")

    print(
        f"gh manual ok: {len(help_files)} commands, {len(topic_files)} topics, "
        f"README/help={ratio:.1%}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
