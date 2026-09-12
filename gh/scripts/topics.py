#!/usr/bin/env python3
"""Render compact shared-topic references from normalized gh help."""

from __future__ import annotations

import re


EXPOSED_TOPICS = ("accessibility", "environment", "exit-codes", "formatting", "mintty")
ENVIRONMENT = {
    ("GH_TOKEN", "GITHUB_TOKEN"): "github.com token; first name wins and overrides stored credentials.",
    ("GH_ENTERPRISE_TOKEN", "GITHUB_ENTERPRISE_TOKEN"): "GitHub Enterprise Server token; first name wins.",
    ("GH_HOST",): "default GitHub hostname when repository context does not supply one.",
    ("GH_REPO",): "default repository as `[HOST/]OWNER/REPO`.",
    ("GH_EDITOR", "GIT_EDITOR", "VISUAL", "EDITOR"): "editor precedence, left to right.",
    ("GH_BROWSER", "BROWSER"): "browser precedence, left to right.",
    ("GH_DEBUG",): "truthy enables debug output; `api` also logs HTTP traffic.",
    ("DEBUG",): "deprecated debug switch.",
    ("GH_PAGER", "PAGER"): "pager precedence, left to right.",
    ("GLAMOUR_STYLE",): "Markdown rendering style.",
    ("NO_COLOR",): "any value disables ANSI color.",
    ("CLICOLOR",): "`0` disables ANSI color.",
    ("CLICOLOR_FORCE",): "nonzero forces color when output is piped.",
    ("GH_COLOR_LABELS",): "show label RGB colors in true-color terminals.",
    ("GH_ACCESSIBLE_COLORS",): "truthy enables customizable 4-bit colors.",
    ("GH_FORCE_TTY",): "force terminal output; number sets columns, percentage scales width.",
    ("GH_NO_UPDATE_NOTIFIER",): "disable daily gh update notices.",
    ("GH_NO_EXTENSION_UPDATE_NOTIFIER",): "disable daily extension update notices.",
    ("GH_EXTENSION",): "set to `1` by gh while invoking an extension.",
    ("GH_CONFIG_DIR",): "configuration directory; otherwise XDG, Windows AppData, or `~/.config/gh`.",
    ("GH_PROMPT_DISABLED",): "disable interactive prompts.",
    ("GH_PATH",): "path to gh when it cannot determine its executable path.",
    ("GH_MDWIDTH",): "maximum Markdown wrap width, capped by terminal width and 120.",
    ("GH_ACCESSIBLE_PROMPTER",): "truthy enables screen-reader-friendly prompts.",
    ("GH_TELEMETRY",): "`log` prints telemetry; `false` or `0` disables it and overrides `DO_NOT_TRACK`.",
    ("DO_NOT_TRACK",): "`true` or `1` disables telemetry unless `GH_TELEMETRY` is set.",
    ("GH_SPINNER_DISABLED",): "truthy replaces animated spinners with text progress.",
}


def text(lines: list[str]) -> str:
    return "\n".join(line.rstrip() for line in lines).rstrip() + "\n"


def source_environment_groups(source: str) -> set[tuple[str, ...]]:
    groups: set[tuple[str, ...]] = set()
    for paragraph in re.split(r"\n\n+", source):
        if not paragraph.startswith("`"):
            continue
        names = tuple(re.findall(r"`([A-Z][A-Z0-9_]*)`", paragraph.split(":", 1)[0]))
        if names:
            groups.add(names)
    return groups


def render_environment(source: str) -> str:
    found = source_environment_groups(source)
    expected = set(ENVIRONMENT)
    if found != expected:
        raise ValueError(f"environment variables changed: added={found - expected}, removed={expected - found}")
    lines = ["# Environment", ""]
    for names, description in ENVIRONMENT.items():
        lines.append(f"- `{', '.join(names)}` — {description}")
    return text(lines)


def render_accessibility(source: str) -> str:
    required = (
        "gh config set accessible_colors enabled",
        "GH_ACCESSIBLE_COLORS=enabled",
        "gh config set color_labels enabled",
        "GH_COLOR_LABELS=enabled",
        "gh config set accessible_prompter enabled",
        "GH_ACCESSIBLE_PROMPTER=enabled",
        "gh config set spinner disabled",
        "GH_SPINNER_DISABLED=yes",
    )
    missing = [item for item in required if item not in source]
    if missing:
        raise ValueError(f"accessibility controls changed: {missing}")
    return text([
        "# Accessibility",
        "",
        "| Need | Config | Environment |",
        "|---|---|---|",
        "| Customizable 4-bit colors | `gh config set accessible_colors enabled` | `GH_ACCESSIBLE_COLORS=enabled` |",
        "| True-color labels | `gh config set color_labels enabled` | `GH_COLOR_LABELS=enabled` |",
        "| Screen-reader-friendly prompts | `gh config set accessible_prompter enabled` | `GH_ACCESSIBLE_PROMPTER=enabled` |",
        "| Text progress instead of spinners | `gh config set spinner disabled` | `GH_SPINNER_DISABLED=yes` |",
    ])


def render_exit_codes(source: str) -> str:
    entries = re.findall(r"- If (.+?), the exit code will be (\d+)", source)
    if len(entries) != 4:
        raise ValueError("exit-code help shape changed")
    lines = ["# Exit codes", "", "| Code | Meaning |", "|---:|---|"]
    lines.extend(f"| {code} | {meaning.capitalize()} |" for meaning, code in entries)
    lines.extend(["", "Commands may define additional exit codes; check that command's details before branching on status."])
    return text(lines)


def render_formatting(source: str) -> str:
    functions = [
        (name, re.sub(r"\s*(?:using )?<https://[^>]+>", "", description))
        for name, description in re.findall(r"^- (`[^`]+`): (.+)$", source, re.MULTILINE)
    ]
    if len(functions) < 10 or not all(flag in source for flag in ("--json", "--jq", "--template")):
        raise ValueError("formatting help shape changed")
    lines = [
        "# Formatting",
        "",
        "For commands supporting structured output:",
        "",
        "- `--json field1,field2` selects fields; pass `--json` without fields to list valid names.",
        "- `--jq '<expr>'` filters JSON with embedded jq; external jq is unnecessary.",
        "- `--template '<template>'` formats JSON with Go templates and the helpers below.",
        "",
        "## Template helpers",
    ]
    lines.extend(f"- {name}: {description}" for name, description in functions)
    lines.extend([
        "",
        "## Minimal patterns",
        "",
        "```bash",
        "gh pr list --json number,title,author",
        "gh pr list --json author --jq '.[].author.login'",
        "gh issue list --json title,url --template '{{range .}}{{hyperlink .url .title}}{{\"\\n\"}}{{end}}'",
        "```",
    ])
    return text(lines)


def render_mintty(source: str) -> str:
    if "MinTTY" not in source or "winpty" not in source:
        raise ValueError("MinTTY help shape changed")
    return text([
        "# MinTTY",
        "",
        "MinTTY can break interactive gh prompts. Prefer, in order:",
        "",
        "1. Enable Git for Windows experimental pseudo-console support.",
        "2. Run Git Bash inside Windows Terminal or another terminal emulator.",
        "3. Prefix with `winpty` as a last resort; UI glitches remain possible.",
    ])


def render_topic(name: str, source: str) -> str | None:
    renderers = {
        "accessibility": render_accessibility,
        "environment": render_environment,
        "exit-codes": render_exit_codes,
        "formatting": render_formatting,
        "mintty": render_mintty,
    }
    renderer = renderers.get(name)
    return renderer(source) if renderer else None
