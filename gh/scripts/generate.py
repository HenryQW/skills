#!/usr/bin/env python3
"""Generate a progressively loadable manual from the installed GitHub CLI."""

from __future__ import annotations

import os
from pathlib import Path
import re
import shutil
import subprocess

from compact import render_help, write_facets


SKILL_DIR = Path(__file__).resolve().parents[1]
REFERENCES = SKILL_DIR / "references"
COMMANDS = REFERENCES / "commands"
TOPICS = REFERENCES / "topics"
COMMAND_ROW = re.compile(r"^  ([a-z][a-z0-9-]*):\s+\S")
EXTENSION_ROW = re.compile(r"^  ([a-z][a-z0-9-]*)\s{2,}\S")
UPPER_HEADING = re.compile(r"^[A-Z][A-Z ]+$")
TITLE_HEADING = re.compile(r"^[A-Za-z][^:]*:$")
SKIP_EXTENSION_SECTIONS = {"Usage:", "Examples:", "Flags:", "Learn more:"}


def run(*args: str) -> str:
    env = os.environ | {
        "GH_PAGER": "cat",
        "PAGER": "cat",
        "NO_COLOR": "1",
        "GH_PROMPT_DISABLED": "1",
    }
    result = subprocess.run(
        ("gh", *args),
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env=env,
    )
    if result.returncode:
        detail = result.stderr.strip() or result.stdout.strip()
        raise RuntimeError(f"gh {' '.join(args)} failed: {detail}")
    return "\n".join(line.rstrip() for line in result.stdout.rstrip().splitlines()) + "\n"


def command_children(help_text: str) -> list[str]:
    """Read child names from gh and Cobra-style command lists."""
    children: list[str] = []
    command_section = False
    extension_section = False

    for line in help_text.splitlines():
        if UPPER_HEADING.fullmatch(line):
            command_section = line.endswith("COMMANDS")
            extension_section = False
            continue
        if TITLE_HEADING.fullmatch(line):
            command_section = False
            extension_section = line not in SKIP_EXTENSION_SECTIONS
            continue

        match = COMMAND_ROW.match(line) if command_section else None
        if match is None and extension_section:
            match = EXTENSION_ROW.match(line)
        if match and match.group(1) not in children:
            children.append(match.group(1))

    return children


def command_file(path: tuple[str, ...], name: str) -> Path:
    return COMMANDS.joinpath(*path, name)


def command_help(path: tuple[str, ...]) -> str:
    return run("--help") if not path else run("help", *path)


def generate_commands() -> list[tuple[tuple[str, ...], str]]:
    pending = [tuple()]
    seen: set[tuple[str, ...]] = set()
    records: list[tuple[tuple[str, ...], str]] = []

    while pending:
        path = pending.pop(0)
        if path in seen:
            continue
        help_text = command_help(path)
        seen.add(path)
        records.append((path, help_text))
        pending.extend((*path, child) for child in command_children(help_text))

    return records


def help_topics(root_help: str) -> list[str]:
    topics: list[str] = []
    active = False
    for line in root_help.splitlines():
        if UPPER_HEADING.fullmatch(line):
            active = line == "HELP TOPICS"
            continue
        if active:
            match = COMMAND_ROW.match(line)
            if match and match.group(1) != "reference":
                topics.append(match.group(1))
    return topics


def main() -> int:
    version = run("--version").splitlines()[0]
    records = generate_commands()
    topics = help_topics(records[0][1])

    shutil.rmtree(COMMANDS, ignore_errors=True)
    shutil.rmtree(TOPICS, ignore_errors=True)
    COMMANDS.mkdir(parents=True)
    TOPICS.mkdir(parents=True)

    manifest = []
    for path, help_text in records:
        target = command_file(path, "help.txt")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(help_text)
        write_facets(target.parent, render_help(help_text, path))
        manifest.append("/".join(path) or ".")

    for topic in topics:
        (TOPICS / f"{topic}.md").write_text(run("help", topic))

    (REFERENCES / "manifest.txt").write_text("\n".join(manifest) + "\n")
    (REFERENCES / "snapshot.txt").write_text(
        f"{version}\n"
        f"commands: {len(records)}\n"
        f"help topics: {len(topics)}\n"
        "Source: recursively generated from installed `gh help`; official command "
        "index checked against https://cli.github.com/manual/gh.\n"
        "The duplicate `gh help reference` topic is omitted because command sources "
        "contain the full help. Local aliases and extensions visible to `gh` are included.\n"
    )
    print(f"generated {len(records)} commands and {len(topics)} topics from {version}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
