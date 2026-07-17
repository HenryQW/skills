#!/usr/bin/env python3
"""Preview or apply the self-contained agent-memory bootstrap."""

from __future__ import annotations

import argparse
import difflib
import hashlib
import json
import os
import tempfile
from collections.abc import Callable
from pathlib import Path, PurePosixPath

from obsidian_project import DECLARATION, resolve_obsidian_project, unsymlinked_path
from trusted_write import WriteTarget, apply_write_plan, sha256_bytes


GLOBAL_START = "<!-- agent-memory:start -->"
GLOBAL_END = "<!-- agent-memory:end -->"
GLOBAL_BLOCK = f"""{GLOBAL_START}
## Agent Memory

If a project `AGENTS.md` defines `OBSIDIAN_PROJECT=${{OBSIDIAN_ROOT}}/<project-path>`, read `${{OBSIDIAN_ROOT}}/agent/knowledge-workflow.md` before loading project memory. Do not infer `OBSIDIAN_PROJECT`. If `OBSIDIAN_ROOT` or a configured memory file is unavailable, report it briefly and continue unless the task depends on it.
{GLOBAL_END}"""

PROGRESS_TEMPLATE = """# Progress

No active task.

Use this ignored file as the local implementation ledger. Distill only durable context with `$agent-memory`.
"""

IGNORED_CONTEXT_FILES = (
    ".context/progress.md",
    ".context/decisions.jsonl",
    ".context/memory-context.md",
    ".context/memory-distill-preview.json",
)

MEMORY_INDEX_TEMPLATE = """---
type: project-note
status: active
tags: []
---
# Memory

**Summary**: Router for approved project decisions and reusable guidance.

<!-- Link approved notes below. Each filename stem is its globally unique topic ID. -->

## Decisions

## Guidance
"""

Change = tuple[Path, bool, str, str]


def resolve_obsidian_root() -> Path:
    value = os.environ.get("OBSIDIAN_ROOT")
    if not value:
        raise SystemExit('OBSIDIAN_ROOT is not set; export OBSIDIAN_ROOT="/absolute/path/to/Obsidian/vault"')
    root = Path(value).expanduser()
    if not root.is_absolute() or not root.is_dir():
        raise SystemExit(f"OBSIDIAN_ROOT must be an existing absolute directory: {root}")
    return root.resolve()


def project_parts(value: str) -> tuple[str, ...]:
    raw = value.strip()
    parts = raw.split("/")
    path = PurePosixPath(raw)
    if (
        not raw
        or path.is_absolute()
        or "\\" in raw
        or any(character in raw for character in ("$", "`"))
        or any(ord(character) < 32 or ord(character) == 127 for character in raw)
        or any(part in {"", ".", ".."} for part in parts)
    ):
        raise SystemExit("--obsidian-project must be a relative path such as Project_Name")
    return tuple(parts)


def file_state(path: Path) -> tuple[bool, str]:
    if path.is_symlink():
        raise SystemExit(f"setup target must not be a symlink: {path}")
    if not path.exists():
        return False, ""
    if not path.is_file():
        raise SystemExit(f"setup target must be a regular file: {path}")
    with path.open(encoding="utf-8", newline="") as handle:
        return True, handle.read()


def read(path: Path) -> str:
    return file_state(path)[1]


def preferred_newline(existing: str) -> str:
    return "\r\n" if existing and existing.count("\r\n") == existing.count("\n") else "\n"


def append_text(existing: str, addition: str) -> str:
    newline = preferred_newline(existing)
    separator = "" if not existing else (newline if existing.endswith("\n") else newline * 2)
    rendered = addition.rstrip().replace("\n", newline)
    return existing + separator + rendered + newline


def render_global_agents(existing: str) -> str:
    has_start = GLOBAL_START in existing
    has_end = GLOBAL_END in existing
    if has_start != has_end or existing.count(GLOBAL_START) > 1 or existing.count(GLOBAL_END) > 1:
        raise SystemExit("~/.codex/AGENTS.md has malformed agent-memory markers")
    if has_start:
        start = existing.index(GLOBAL_START)
        end = existing.find(GLOBAL_END, start)
        if end < 0:
            raise SystemExit("~/.codex/AGENTS.md has malformed agent-memory markers")
        end += len(GLOBAL_END)
        expected = GLOBAL_BLOCK.replace("\n", preferred_newline(existing))
        if existing[start:end] != expected:
            raise SystemExit("~/.codex/AGENTS.md has a conflicting agent-memory block")
        return existing
    if "knowledge-workflow.md" in existing:
        raise SystemExit("~/.codex/AGENTS.md has unmarked agent-memory instructions; reconcile them first")
    return append_text(existing, GLOBAL_BLOCK)


def render_project_agents(existing: str, relative: str) -> str:
    expected = f"${{OBSIDIAN_ROOT}}/{relative}"
    matches = list(DECLARATION.finditer(existing))
    if len(matches) > 1:
        raise SystemExit("project AGENTS.md has multiple OBSIDIAN_PROJECT declarations")
    if matches:
        if matches[0].group(1).strip() != expected:
            raise SystemExit("project AGENTS.md has a conflicting OBSIDIAN_PROJECT declaration")
        return existing
    return append_text(existing, f"OBSIDIAN_PROJECT={expected}")


def render_gitignore(existing: str) -> str:
    present = set(existing.splitlines())
    missing = [item for item in IGNORED_CONTEXT_FILES if item not in present]
    if not missing:
        return existing
    return append_text(existing, "# Agent local context\n" + "\n".join(missing))


def add_change(changes: list[Change], path: Path, after: str, *, conflict: bool = False) -> None:
    existed, before = file_state(path)
    if conflict and existed and before != after:
        raise SystemExit(f"refusing to overwrite existing file: {path}")
    if not existed or before != after:
        changes.append((path, existed, before, after))


def add_rendered_change(changes: list[Change], path: Path, render: Callable[[str], str]) -> None:
    existed, before = file_state(path)
    after = render(before)
    if not existed or before != after:
        changes.append((path, existed, before, after))


def validate_directory_path(path: Path) -> None:
    current = Path(path.anchor)
    for part in path.parts[1:]:
        current /= part
        if current.is_symlink() or (current.exists() and not current.is_dir()):
            raise SystemExit(f"setup directory is not a real directory: {current}")


def plan_setup(
    project_root: Path,
    obsidian_root: Path,
    relative_parts: tuple[str, ...],
    codex_home: Path,
) -> tuple[list[Path], list[Change]]:
    project_root = project_root.resolve()
    obsidian_root = obsidian_root.resolve()
    codex_home = codex_home.resolve()
    if not project_root.is_dir():
        raise SystemExit(f"project root does not exist: {project_root}")
    relative = "/".join(relative_parts)
    obsidian_project = unsymlinked_path(obsidian_root, *relative_parts)
    memory_dir = unsymlinked_path(obsidian_project, "Agent", "Memory")
    workflow = unsymlinked_path(obsidian_root, "agent", "knowledge-workflow.md")
    workflow_template = (Path(__file__).parent.parent / "assets" / "knowledge-workflow.md").read_text(encoding="utf-8")

    expected_dirs = [
        codex_home,
        workflow.parent,
        project_root / ".context",
        unsymlinked_path(memory_dir, "Decisions"),
        unsymlinked_path(memory_dir, "Guidance"),
    ]
    missing_dirs: list[Path] = []
    for path in expected_dirs:
        validate_directory_path(path)
        if not path.exists():
            missing_dirs.append(path)

    changes: list[Change] = []
    global_agents = codex_home / "AGENTS.md"
    project_agents = project_root / "AGENTS.md"
    add_rendered_change(changes, global_agents, render_global_agents)
    add_change(changes, workflow, workflow_template, conflict=True)
    add_rendered_change(changes, project_agents, lambda text: render_project_agents(text, relative))
    progress = project_root / ".context" / "progress.md"
    progress_exists, _ = file_state(progress)
    if not progress_exists:
        add_change(changes, progress, PROGRESS_TEMPLATE)
    add_rendered_change(changes, project_root / ".gitignore", render_gitignore)
    index = unsymlinked_path(memory_dir, "index.md")
    index_exists, _ = file_state(index)
    if not index_exists:
        add_change(changes, index, MEMORY_INDEX_TEMPLATE)
    return missing_dirs, changes


def emit_preview(directories: list[Path], changes: list[Change]) -> None:
    for path in directories:
        print(f"PREVIEW mkdir={path}")
    for path, _, before, after in changes:
        print(f"PREVIEW file={path}")
        print(
            "".join(
                difflib.unified_diff(
                    before.splitlines(keepends=True),
                    after.splitlines(keepends=True),
                    fromfile=f"{path} (current)",
                    tofile=f"{path} (proposed)",
                )
            ),
            end="",
        )


def confirmation_hash(directories: list[Path], changes: list[Change]) -> str:
    payload = {
        "directories": [str(path) for path in directories],
        "changes": [[str(path), existed, before, after] for path, existed, before, after in changes],
    }
    rendered = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(rendered.encode()).hexdigest()


def apply_setup(
    roots: tuple[Path, ...],
    directories: list[Path],
    changes: list[Change],
    write_plan=apply_write_plan,
) -> None:
    write_plan(
        roots=roots,
        directories=directories,
        targets=tuple(
            WriteTarget(
                path,
                sha256_bytes(before.encode()) if existed else None,
                after.encode(),
            )
            for path, existed, before, after in changes
        ),
    )


def self_test() -> int:
    with tempfile.TemporaryDirectory() as raw:
        root = Path(raw)
        vault = root / "vault"
        project = root / "repo"
        codex_home = root / "codex"
        vault.mkdir()
        project.mkdir()
        codex_home.mkdir()
        (project / "AGENTS.md").write_text("# Project\n", encoding="utf-8")
        (project / ".gitignore").write_text("dist/\n", encoding="utf-8")
        (codex_home / "AGENTS.md").write_text("# Global\n", encoding="utf-8")

        previous = os.environ.pop("OBSIDIAN_ROOT", None)
        try:
            try:
                resolve_obsidian_root()
            except SystemExit as exc:
                assert "is not set" in str(exc)
            else:
                raise AssertionError("accepted missing OBSIDIAN_ROOT")
            os.environ["OBSIDIAN_ROOT"] = str(vault)
            obsidian_root = resolve_obsidian_root()
            roots = (project.resolve(), obsidian_root, codex_home.resolve())
            parts = project_parts("Project_Name")
            directories, changes = plan_setup(project, obsidian_root, parts, codex_home)
            assert directories and changes
            assert not (vault / "Project_Name").exists()

            token = confirmation_hash(directories, changes)
            assert len(token) == 64
            workflow = vault / "agent" / "knowledge-workflow.md"
            workflow.parent.mkdir()
            workflow.write_text("", encoding="utf-8")
            try:
                apply_setup(roots, directories, changes)
            except SystemExit as exc:
                assert "changed after planning" in str(exc)
            else:
                raise AssertionError("overwrote an empty file created after preview")
            try:
                plan_setup(project, obsidian_root, parts, codex_home)
            except SystemExit as exc:
                assert "refusing to overwrite existing file" in str(exc)
            else:
                raise AssertionError("accepted an empty conflicting workflow")
            workflow.unlink()
            workflow.parent.rmdir()
            directories, changes = plan_setup(project, obsidian_root, parts, codex_home)
            assert confirmation_hash(directories, changes) == token

            gitignore = project / ".gitignore"
            gitignore.write_text("dist/\n.cache/\n", encoding="utf-8")
            try:
                apply_setup(roots, directories, changes)
            except SystemExit as exc:
                assert "changed after planning" in str(exc)
            else:
                raise AssertionError("applied a stale setup plan")
            assert not (vault / "Project_Name").exists()
            gitignore.write_text("dist/\n", encoding="utf-8")
            directories, changes = plan_setup(project, obsidian_root, parts, codex_home)
            recorded_plans = []

            def recording_write_plan(**plan):
                recorded_plans.append(plan)
                return apply_write_plan(**plan)

            apply_setup(roots, directories, changes, write_plan=recording_write_plan)
            assert len(recorded_plans) == 1
            assert tuple(recorded_plans[0]["directories"]) == tuple(directories)
            assert [target.path for target in recorded_plans[0]["targets"]] == [change[0] for change in changes]
            assert GLOBAL_BLOCK in read(codex_home / "AGENTS.md")
            assert "OBSIDIAN_PROJECT=${OBSIDIAN_ROOT}/Project_Name" in read(project / "AGENTS.md")
            assert resolve_obsidian_project(project) == (vault / "Project_Name").resolve()
            assert read(vault / "agent" / "knowledge-workflow.md").startswith("# Knowledge Workflow")
            assert (vault / "Project_Name" / "Agent" / "Memory" / "Decisions").is_dir()
            assert (vault / "Project_Name" / "Agent" / "Memory" / "Guidance").is_dir()
            assert all(item in read(project / ".gitignore") for item in IGNORED_CONTEXT_FILES)

            directories, changes = plan_setup(project, obsidian_root, parts, codex_home)
            assert directories == [] and changes == []

            global_path = codex_home / "AGENTS.md"
            global_path.write_text(read(global_path).replace("## Agent Memory", "## Changed"), encoding="utf-8")
            try:
                plan_setup(project, obsidian_root, parts, codex_home)
            except SystemExit as exc:
                assert "conflicting agent-memory block" in str(exc)
            else:
                raise AssertionError("accepted conflicting global memory instructions")

            try:
                render_global_agents(f"{GLOBAL_END}\n{GLOBAL_START}\n")
            except SystemExit as exc:
                assert "malformed agent-memory markers" in str(exc)
            else:
                raise AssertionError("accepted reversed global markers")

            rendered = render_project_agents("# Project\r\n", "Project_Name")
            assert rendered == "# Project\r\n\r\nOBSIDIAN_PROJECT=${OBSIDIAN_ROOT}/Project_Name\r\n"
            global_crlf = render_global_agents("# Global\r\n")
            assert render_global_agents(global_crlf) == global_crlf

            blocked_vault = root / "blocked-vault"
            blocked_vault.mkdir()
            (blocked_vault / "Project_Name").write_text("not a directory", encoding="utf-8")
            try:
                plan_setup(project, blocked_vault, parts, codex_home)
            except SystemExit as exc:
                assert "setup directory is not a real directory" in str(exc)
            else:
                raise AssertionError("accepted an intermediate file as a directory")

            for invalid in (
                "",
                "/absolute",
                "../escape",
                "Project//Name",
                "Project\\Name",
                "${OBSIDIAN_ROOT}/Project_Name",
                "Project`Name",
                "$HOME/Project_Name",
                "Project\nName",
            ):
                try:
                    project_parts(invalid)
                except SystemExit:
                    pass
                else:
                    raise AssertionError(f"accepted invalid project path: {invalid}")
            relative = "/".join(project_parts("Project_Name"))
            declaration = render_project_agents("", relative).strip()
            match = DECLARATION.fullmatch(declaration)
            assert match and match.group(1) == "${OBSIDIAN_ROOT}/Project_Name"
        finally:
            if previous is None:
                os.environ.pop("OBSIDIAN_ROOT", None)
            else:
                os.environ["OBSIDIAN_ROOT"] = previous
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", default=".")
    parser.add_argument("--obsidian-project")
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--confirm")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        return self_test()
    if not args.obsidian_project:
        parser.error("--obsidian-project is required")
    if args.apply and not args.confirm:
        parser.error("--apply requires --confirm from the latest preview")
    if args.confirm and not args.apply:
        parser.error("--confirm requires --apply")

    project_root = Path(args.project_root).resolve()
    obsidian_root = resolve_obsidian_root()
    codex_home = Path(os.environ.get("CODEX_HOME", Path.home() / ".codex")).expanduser().resolve()
    directories, changes = plan_setup(project_root, obsidian_root, project_parts(args.obsidian_project), codex_home)
    if not directories and not changes:
        print("setup=UNCHANGED")
        return 0
    token = confirmation_hash(directories, changes)
    if not args.apply:
        emit_preview(directories, changes)
        print(f"setup=PREVIEW changes={len(directories) + len(changes)} confirm={token}")
        return 0
    if args.confirm != token:
        raise SystemExit("setup changed after preview; preview again")
    apply_setup((project_root, obsidian_root, codex_home), directories, changes)
    print(f"setup=APPLIED changes={len(directories) + len(changes)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
