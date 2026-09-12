#!/usr/bin/env python3
"""Render raw GitHub CLI help as progressively loadable command facets."""

from __future__ import annotations

from pathlib import Path
import re


FACETS = ("README.md", "options.md", "examples.md", "details.md")
BUILTIN_SECTIONS = {
    "USAGE",
    "ALIASES",
    "FLAGS",
    "INHERITED FLAGS",
    "ARGUMENTS",
    "ENVIRONMENT VARIABLES",
    "EXAMPLES",
    "JSON FIELDS",
    "LEARN MORE",
    "HELP TOPICS",
}
GENERIC_LEARN_MORE = {
    "Use `gh <command> <subcommand> --help` for more information about a command.",
    "Read the manual at https://cli.github.com/manual",
    "Learn about exit codes using `gh help exit-codes`",
    "Learn about accessibility experiences using `gh help accessibility`",
}
GENERIC_COBRA_HELP = re.compile(r'^Use "gh .+ \[command\] --help" for more information about a command\.$')
CHILD_ROW = re.compile(r"^  ([a-z][a-z0-9-]*):?\s{2,}(.+)$")


def clean(lines: list[str]) -> list[str]:
    """Strip trailing whitespace and outer blank lines."""
    lines = [line.rstrip() for line in lines]
    while lines and not lines[0]:
        lines.pop(0)
    while lines and not lines[-1]:
        lines.pop()
    return lines


def text(lines: list[str]) -> str:
    lines = clean(lines)
    return "\n".join(lines) + "\n" if lines else ""


def split_sections(help_text: str) -> tuple[list[str], list[tuple[str, list[str]]]]:
    """Split gh and Cobra help without treating prose labels as headings."""
    preamble: list[str] = []
    sections: list[tuple[str, list[str]]] = []
    current = preamble

    for raw in help_text.splitlines():
        line = raw.rstrip()
        heading: str | None = None
        if line in BUILTIN_SECTIONS or (line.isupper() and line.endswith(" COMMANDS")):
            heading = line
        elif line in {"Usage:", "Examples:", "Flags:", "Learn more:"}:
            heading = line[:-1].upper().replace(" ", "_")
        elif line in {"Stack management:", "Remote operations:", "Navigation:", "Utilities:"}:
            heading = line[:-1]

        if heading is not None:
            current = []
            sections.append((heading, current))
        else:
            current.append(line)

    return clean(preamble), [(name, clean(body)) for name, body in sections]


def first_sentence(lines: list[str]) -> str:
    if not lines:
        return ""
    first_paragraph: list[str] = []
    for line in lines:
        if not line:
            break
        first_paragraph.append(line.strip())
    joined = " ".join(first_paragraph)
    match = re.search(r"[.!?](?:\s|$)", joined)
    return joined[: match.end()].strip() if match else joined


def compact_usage(lines: list[str]) -> list[str]:
    return [line.strip() for line in lines if line.strip()]


def compact_aliases(lines: list[str]) -> list[str]:
    return [line.strip() for line in lines if line.strip()]


def child_rows(sections: list[tuple[str, list[str]]]) -> list[tuple[str, str]]:
    rows: list[tuple[str, str]] = []
    for name, body in sections:
        if not (name.endswith("COMMANDS") or name in {"Stack management", "Remote operations", "Navigation", "Utilities"}):
            continue
        for line in body:
            match = CHILD_ROW.match(line)
            if match:
                rows.append((match.group(1), match.group(2).strip()))
    return rows


def render_help(help_text: str, command_path: tuple[str, ...]) -> dict[str, str]:
    """Return deterministic compact files for one lossless help.txt source."""
    preamble, sections = split_sections(help_text)
    command = "gh" + (" " + " ".join(command_path) if command_path else "")
    summary = first_sentence(preamble)
    usage: list[str] = []
    aliases: list[str] = []
    option_blocks: list[tuple[str, list[str]]] = []
    example_lines: list[str] = []
    detail_blocks: list[tuple[str, list[str]]] = []

    if preamble:
        collapsed = " ".join(line.strip() for line in preamble if line)
        if collapsed != summary:
            detail_blocks.append(("Description", preamble))

    for name, body in sections:
        if name == "USAGE":
            usage.extend(compact_usage(body))
        elif name == "ALIASES":
            aliases.extend(compact_aliases(body))
        elif name in {"FLAGS", "INHERITED FLAGS"}:
            body = [line for line in body if not GENERIC_COBRA_HELP.match(line.strip())]
            if clean(body):
                option_blocks.append((name.title(), body))
        elif name == "EXAMPLES":
            example_lines.extend(body)
        elif name == "LEARN MORE":
            specific = [line for line in body if line.strip() not in GENERIC_LEARN_MORE]
            if clean(specific):
                detail_blocks.append(("Learn more", specific))
        elif name.endswith("COMMANDS") or name in {"Stack management", "Remote operations", "Navigation", "Utilities"}:
            continue
        elif body:
            detail_blocks.append((name.title(), body))

    readme = [f"# {command}"]
    if summary:
        readme.extend(["", summary])
    if usage:
        readme.extend(["", "**Usage:** " + " / ".join(f"`{item}`" for item in usage)])
    if aliases:
        readme.extend(["", "**Aliases:** " + ", ".join(f"`{item}`" for item in aliases)])

    children = child_rows(sections)
    if children:
        readme.extend(["", "## Commands"])
        for name, description in children:
            readme.append(f"- [`{name}`]({name}/) — {description}")

    files: dict[str, str] = {}
    if option_blocks:
        lines = ["# Options"]
        for heading, body in option_blocks:
            lines.extend(["", f"## {heading}", "", *body])
        files["options.md"] = text(lines)
    if clean(example_lines):
        files["examples.md"] = text(["# Examples", "", *example_lines])
    if detail_blocks:
        lines = ["# Details"]
        for heading, body in detail_blocks:
            lines.extend(["", f"## {heading}", "", *body])
        files["details.md"] = text(lines)

    if files:
        readme.extend(["", "## More"])
        labels = {"options.md": "Options", "examples.md": "Examples", "details.md": "Details"}
        for filename in ("options.md", "examples.md", "details.md"):
            if filename in files:
                readme.append(f"- [{labels[filename]}]({filename})")
    files["README.md"] = text(readme)
    return {name: files[name] for name in FACETS if name in files}


def write_facets(directory: Path, rendered: dict[str, str]) -> None:
    for name in FACETS:
        target = directory / name
        if name in rendered:
            target.write_text(rendered[name])
        elif target.exists():
            target.unlink()


def compact_help_file(help_path: Path, command_path: tuple[str, ...] | None = None) -> dict[str, str]:
    if command_path is None:
        command_path = tuple(help_path.parent.parts)
    rendered = render_help(help_path.read_text(), command_path)
    write_facets(help_path.parent, rendered)
    return rendered
