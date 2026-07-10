"""Resolve the project's Obsidian folder from its AGENTS.md declaration."""

from __future__ import annotations

import os
import re
from pathlib import Path


DECLARATION = re.compile(
    r"(?m)^[ \t]*(?:[-*][ \t]+)?`?OBSIDIAN_PROJECT[ \t]*=[ \t]*`?([^`\n]+?)`?[ \t]*$"
)


def resolve_obsidian_project(project_root: Path) -> Path:
    path = project_root / "AGENTS.md"
    text = path.read_text(encoding="utf-8") if path.exists() else ""
    match = DECLARATION.search(text)
    if not match:
        raise SystemExit(f"{path}: add OBSIDIAN_PROJECT=${{OBSIDIAN_ROOT}}/<project-path>")
    value = match.group(1).strip()
    if not value.startswith("${OBSIDIAN_ROOT}/"):
        raise SystemExit(f"{path}: OBSIDIAN_PROJECT must start with ${{OBSIDIAN_ROOT}}/")
    root_value = os.environ.get("OBSIDIAN_ROOT")
    if not root_value:
        raise SystemExit("OBSIDIAN_ROOT is not set")
    root = Path(root_value).expanduser().resolve()
    project = Path(os.path.expandvars(value)).expanduser().resolve()
    try:
        project.relative_to(root)
    except ValueError:
        raise SystemExit(f"{path}: OBSIDIAN_PROJECT must stay under OBSIDIAN_ROOT") from None
    return project


def resolve_memory_index(project_root: Path) -> Path:
    return resolve_obsidian_project(project_root) / "Agent" / "Memory" / "index.md"


def topic_slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.casefold()).strip("-") or "memory"


def unsymlinked_path(root: Path, *parts: str) -> Path:
    path = root.resolve()
    for part in parts:
        path /= part
        if path.is_symlink() or path.resolve() != path:
            raise SystemExit(f"memory path must not contain symlinks: {path}")
    return path
