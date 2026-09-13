#!/usr/bin/env python3
"""Validate the generated, progressively loadable GitHub CLI manual."""

from pathlib import Path
import re
import sys


sys.path.insert(0, str(Path(__file__).parent))
from compact import (  # noqa: E402
    FACETS,
    GENERIC_COBRA_HELP,
    HELP_OPTION,
    render_help,
    split_sections,
)
from topics import EXPOSED_TOPICS, render_topic  # noqa: E402


ROOT = Path(__file__).resolve().parents[1]
REFERENCES = ROOT / "references"
COMMANDS = REFERENCES / "commands"
TOPICS = REFERENCES / "topics"
TOPIC_SOURCES = REFERENCES / "topic-sources"


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
    version = snapshot.splitlines()[0].removeprefix("gh version ")
    repository_readme = (ROOT.parent / "README.md").read_text()
    if f"GitHub CLI {version}" not in repository_readme:
        raise ValueError("root README does not identify the snapshot gh version")
    for path in (ROOT / "references").rglob("*"):
        if path.is_file() and "Read the manual at " in path.read_text():
            raise ValueError(f"external CLI manual link present: {path.relative_to(ROOT)}")

    help_files = sorted(COMMANDS.rglob("help.txt"))
    topic_files = sorted(TOPICS.glob("*.md"))
    topic_sources = sorted(TOPIC_SOURCES.glob("*.txt"))
    manifest = (REFERENCES / "manifest.txt").read_text().splitlines()

    command_count = recorded_count("commands", snapshot)
    topic_count = recorded_count("help topics", snapshot)
    compact_topic_count = recorded_count("compact topics", snapshot)
    if len(help_files) != command_count or len(manifest) != command_count:
        raise ValueError("command inventory does not match snapshot")
    if len(topic_sources) != topic_count:
        raise ValueError("help-topic source inventory does not match snapshot")
    if len(topic_files) != compact_topic_count or {
        path.stem for path in topic_files
    } != set(EXPOSED_TOPICS):
        raise ValueError("compact topic inventory does not match snapshot")
    if list(TOPICS.glob("*.txt")) or list(TOPIC_SOURCES.glob("*.md")):
        raise ValueError("topic source and summary formats are mixed")

    expected_manifest = ["/".join(command_path(path)) or "." for path in help_files]
    if sorted(manifest) != sorted(expected_manifest):
        raise ValueError("manifest does not match command directories")

    readme_bytes = 0
    help_bytes = 0
    for help_path in help_files:
        raw = help_path.read_text()
        expected = render_help(raw, command_path(help_path))
        directory = help_path.parent
        if (directory / "options.md").exists():
            raise ValueError(f"standalone options remain: {directory.relative_to(ROOT)}")
        actual_names = {name for name in FACETS if (directory / name).is_file()}
        if actual_names != set(expected):
            raise ValueError(f"facet inventory drift: {directory.relative_to(ROOT)}")
        for name, expected_content in expected.items():
            target = directory / name
            actual = target.read_text()
            if actual != expected_content:
                raise ValueError(f"generated facet drift: {target.relative_to(ROOT)}")
            assert_clean(target, actual)
        readme_content = (directory / "README.md").read_text()
        if any(HELP_OPTION.fullmatch(line.strip()) for line in readme_content.splitlines()):
            raise ValueError(f"universal --help duplicated in {directory.relative_to(ROOT)}")
        for section, lines in split_sections(raw)[1]:
            if section not in {"FLAGS", "INHERITED FLAGS"}:
                continue
            for line in lines:
                if not line or HELP_OPTION.fullmatch(line.strip()) or GENERIC_COBRA_HELP.match(line.strip()):
                    continue
                if line not in readme_content.splitlines():
                    raise ValueError(f"option missing from {directory.relative_to(ROOT)}: {line.strip()}")

        readme = directory / "README.md"
        if readme.stat().st_size >= help_path.stat().st_size:
            raise ValueError(f"README is not smaller than help.txt: {directory.relative_to(ROOT)}")
        readme_bytes += readme.stat().st_size
        help_bytes += help_path.stat().st_size

    ratio = readme_bytes / help_bytes
    if ratio > 0.50:
        raise ValueError(f"aggregate README/help ratio exceeds 50%: {ratio:.1%}")

    topic_bytes = 0
    topic_source_bytes = 0
    for source_path in topic_sources:
        source = source_path.read_text()
        expected = render_topic(source_path.stem, source)
        summary_path = TOPICS / f"{source_path.stem}.md"
        if expected is None:
            if summary_path.exists():
                raise ValueError(f"redundant topic exposed: {summary_path.relative_to(ROOT)}")
        else:
            actual = summary_path.read_text()
            if actual != expected:
                raise ValueError(f"compact topic drift: {summary_path.relative_to(ROOT)}")
            assert_clean(summary_path, actual)
            topic_bytes += summary_path.stat().st_size
        topic_source_bytes += source_path.stat().st_size

    topic_ratio = topic_bytes / topic_source_bytes
    if topic_ratio > 0.40:
        raise ValueError(f"compact topic/source ratio exceeds 40%: {topic_ratio:.1%}")

    print(
        f"gh manual ok: {len(help_files)} commands, {len(topic_files)} compact topics, "
        f"README/help={ratio:.1%}, topics/source={topic_ratio:.1%}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
