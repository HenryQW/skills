#!/usr/bin/env python3
"""Install project agent-memory plumbing."""

from __future__ import annotations

import argparse
import os
import tempfile
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[1]
AGENTS_SNIPPETS = SKILL_ROOT / "references" / "agents.md"
MEMORY_ROUTER_FILENAME = "Memory Router.md"

PROGRESS_TEMPLATE = """# Progress

No active task.

Use this file as the local task ledger during implementation.

## Notes

- Keep this file local. Distill durable context with `$agent-memory` when requested.
"""


MEMORY_ROUTER_TEMPLATE = """# Memory Router

Summary: Durable context for future agents. Load only matching notes; do not load this full folder by default.
Keywords: agent memory, guidance, mistakes, preferences

## Loading Rule

Read this router before non-trivial project work, then open only the memory notes whose title, summary, or keywords match the task.

Memory notes can include history, mistakes to avoid, rules, coding style, library preferences, and validation paths.

When `$agent-memory` is invoked or progress distillation is requested, agents should distill `.context/progress.md` into a real memory note only when it contains durable context future agents would otherwise rediscover. No memory should be written for routine progress.

## Memory

No active memory yet.
"""


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", default=".")
    parser.add_argument("--agent-path")
    parser.add_argument("--instruction-file", default="AGENTS.md")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()

    if args.self_test:
        return self_test()

    if not args.agent_path:
        parser.error("--agent-path is required unless --self-test is set")

    project_root = Path(args.project_root).resolve()
    memory_root = parse_memory_root(parser)
    agent_path = Path(os.path.expandvars(args.agent_path)).resolve()
    require_under_memory_root(parser, agent_path, memory_root)
    instruction_path = project_root / args.instruction_file

    install_agent_memory(project_root, agent_path, instruction_path)

    print("project agent memory setup complete")
    return 0


def install_agent_memory(project_root: Path, agent_path: Path, instruction_path: Path) -> None:
    ensure_progress(project_root)
    ensure_gitignore(project_root)
    ensure_memory_router(agent_path)
    ensure_agents(instruction_path, memory_ref(memory_router_path(agent_path)), agent_path)


def parse_memory_root(parser: argparse.ArgumentParser) -> Path:
    root = os.environ.get("AGENT_MEMORY_ROOT")
    if not root:
        parser.error("set AGENT_MEMORY_ROOT to the markdown root before running setup")
    return Path(root).expanduser().resolve()


def require_under_memory_root(parser: argparse.ArgumentParser, path: Path, root: Path) -> None:
    try:
        path.relative_to(root)
    except ValueError:
        parser.error("--agent-path must be under AGENT_MEMORY_ROOT")


def memory_ref(path: Path) -> str:
    rel = path.resolve().relative_to(Path(os.environ["AGENT_MEMORY_ROOT"]).expanduser().resolve())
    return "${AGENT_MEMORY_ROOT}/" + rel.as_posix()


def ensure_progress(project_root: Path) -> None:
    progress = project_root / ".context" / "progress.md"
    progress.parent.mkdir(parents=True, exist_ok=True)
    if not progress.exists():
        progress.write_text(PROGRESS_TEMPLATE, encoding="utf-8")


def ensure_gitignore(project_root: Path) -> None:
    gitignore = project_root / ".gitignore"
    text = gitignore.read_text(encoding="utf-8") if gitignore.exists() else ""
    if ".context/progress.md" in text.splitlines():
        return
    suffix = "" if not text or text.endswith("\n") else "\n"
    gitignore.write_text(
        text + suffix + "\n# Agent local progress\n.context/progress.md\n",
        encoding="utf-8",
    )


def memory_router_path(agent_path: Path) -> Path:
    return agent_path / "Memory" / MEMORY_ROUTER_FILENAME


def ensure_memory_router(agent_path: Path) -> None:
    memory = agent_path / "Memory"
    memory.mkdir(parents=True, exist_ok=True)
    router = memory_router_path(agent_path)
    legacy_index = memory / "index.md"
    if router.exists() and legacy_index.exists():
        migrated_index = migrate_legacy_index(legacy_index.read_text(encoding="utf-8"))
        if router.read_text(encoding="utf-8") == migrated_index:
            legacy_index.unlink()
            return
        raise RuntimeError(
            f"both {MEMORY_ROUTER_FILENAME} and index.md exist with different content; "
            "merge them manually"
        )
    if not router.exists() and legacy_index.exists():
        router.write_text(migrate_legacy_index(legacy_index.read_text(encoding="utf-8")), encoding="utf-8")
        legacy_index.unlink()
        return
    if not router.exists():
        router.write_text(MEMORY_ROUTER_TEMPLATE, encoding="utf-8")


def migrate_legacy_index(text: str) -> str:
    text = text.replace("# Agent Memory", "# Memory Router", 1)
    text = text.replace("Read this index", "Read this router", 1)
    return text


def ensure_agents(path: Path, memory_router_ref: str, agent_path: Path) -> None:
    text = path.read_text(encoding="utf-8") if path.exists() else "# AGENTS.md\n"
    text = ensure_section(text, "Context and precedence")
    text = ensure_section(text, "Execution")

    snippets = load_agents_snippets(memory_router_ref, memory_ref(agent_path / "Memory"))
    text = remove_generated_memory_lines(text)
    context_line = snippets["Context and precedence item"]
    text = ensure_before_project_work_item(text, context_line)

    text = ensure_section_bullet(text, "Execution", snippets["Execution item"])

    path.write_text(text, encoding="utf-8")


def load_agents_snippets(memory_router_ref: str, memory_dir_ref: str) -> dict[str, str]:
    text = AGENTS_SNIPPETS.read_text(encoding="utf-8")
    snippets = {
        "Context and precedence item": extract_fenced_block(text, "Context and precedence item"),
        "Execution item": extract_fenced_block(text, "Execution item"),
    }
    return {
        key: value.format(
            memory_router_ref=memory_router_ref,
            memory_dir_ref=memory_dir_ref,
        )
        for key, value in snippets.items()
    }


def extract_fenced_block(text: str, heading: str) -> str:
    marker = f"## {heading}"
    start = text.index(marker)
    fence_start = text.index("```md\n", start) + len("```md\n")
    fence_end = text.index("\n```", fence_start)
    return text[fence_start:fence_end]


def remove_generated_memory_lines(text: str) -> str:
    lines = text.splitlines()
    execution_start = find_section_start(lines, "Execution")
    execution_end = find_next_section(lines, execution_start) if execution_start is not None else -1
    context_start = find_section_start(lines, "Context and precedence")
    context_end = find_next_section(lines, context_start) if context_start is not None else -1
    kept = []
    for i, line in enumerate(lines):
        in_execution = execution_start is not None and execution_start < i < execution_end
        in_context = context_start is not None and context_start < i < context_end
        generated_execution = (
            in_execution
            and line.startswith("- When `$agent-memory` is invoked or progress distillation is requested, ")
            and ".context/progress.md" in line
            and "future agents would otherwise rediscover" in line
            and "Skip routine progress" in line
        )
        generated_context = (
            in_context
            and line.strip().startswith("- `")
            and (
                "/Agent/Memory/index.md`" in line
                or f"/Agent/Memory/{MEMORY_ROUTER_FILENAME}`" in line
            )
        )
        if not (generated_execution or generated_context):
            kept.append(line)
    return "\n".join(kept) + "\n"


def self_test() -> int:
    previous_root = os.environ.get("AGENT_MEMORY_ROOT")
    with tempfile.TemporaryDirectory() as raw_tmp:
        tmp = Path(raw_tmp)
        memory_root = tmp / "memory"
        fresh_project_root = tmp / "fresh-repo"
        fresh_agent_path = memory_root / "projects" / "Fresh" / "Agent"
        fresh_instruction_path = fresh_project_root / "AGENTS.md"
        legacy_project_root = tmp / "legacy-repo"
        legacy_agent_path = memory_root / "projects" / "Example" / "Agent"
        legacy_memory_dir = legacy_agent_path / "Memory"
        legacy_instruction_path = legacy_project_root / "AGENTS.md"
        duplicate_project_root = tmp / "duplicate-repo"
        duplicate_agent_path = memory_root / "projects" / "Duplicate" / "Agent"
        duplicate_memory_dir = duplicate_agent_path / "Memory"
        duplicate_instruction_path = duplicate_project_root / "AGENTS.md"
        conflict_project_root = tmp / "conflict-repo"
        conflict_agent_path = memory_root / "projects" / "Conflict" / "Agent"
        conflict_memory_dir = conflict_agent_path / "Memory"
        conflict_instruction_path = conflict_project_root / "AGENTS.md"
        fresh_project_root.mkdir()
        legacy_project_root.mkdir()
        duplicate_project_root.mkdir()
        conflict_project_root.mkdir()
        legacy_memory_dir.mkdir(parents=True)
        duplicate_memory_dir.mkdir(parents=True)
        conflict_memory_dir.mkdir(parents=True)
        old_index = (
            "# Agent Memory\n\n"
            "Summary: Durable context for future agents.\n\n"
            "## Loading Rule\n\n"
            "Read this index before non-trivial project work.\n\n"
            "## Memory\n\n"
            "- Existing note.\n"
        )
        router_equivalent = migrate_legacy_index(old_index)
        (legacy_memory_dir / "index.md").write_text(
            old_index,
            encoding="utf-8",
        )
        (duplicate_memory_dir / "index.md").write_text(old_index, encoding="utf-8")
        (duplicate_memory_dir / MEMORY_ROUTER_FILENAME).write_text(router_equivalent, encoding="utf-8")
        (conflict_memory_dir / "index.md").write_text(old_index, encoding="utf-8")
        (conflict_memory_dir / MEMORY_ROUTER_FILENAME).write_text("# Memory Router\n\nDifferent.\n", encoding="utf-8")
        legacy_instruction_path.write_text(
            "# AGENTS.md\n\n"
            "## Context and precedence\n\n"
            "- Before project work, read:\n"
            "  - `${AGENT_MEMORY_ROOT}/projects/Example/Agent/Memory/index.md`\n",
            encoding="utf-8",
        )

        try:
            os.environ["AGENT_MEMORY_ROOT"] = os.fspath(memory_root)
            install_agent_memory(fresh_project_root, fresh_agent_path, fresh_instruction_path)

            assert (fresh_project_root / ".context" / "progress.md").exists()
            assert ".context/progress.md" in (fresh_project_root / ".gitignore").read_text(encoding="utf-8")
            assert memory_router_path(fresh_agent_path).exists()
            fresh_router_text = memory_router_path(fresh_agent_path).read_text(encoding="utf-8")
            assert fresh_router_text.startswith("# Memory Router")
            assert "Read this router" in fresh_router_text
            assert "Read this index" not in fresh_router_text

            install_agent_memory(legacy_project_root, legacy_agent_path, legacy_instruction_path)

            assert memory_router_path(legacy_agent_path).exists()
            assert not (legacy_agent_path / "Memory" / "index.md").exists()
            legacy_router_text = memory_router_path(legacy_agent_path).read_text(encoding="utf-8")
            assert legacy_router_text.startswith("# Memory Router")
            assert "Read this router" in legacy_router_text
            assert "Read this index" not in legacy_router_text
            assert "Existing note" in legacy_router_text

            instructions = legacy_instruction_path.read_text(encoding="utf-8")
            assert "Agent/Memory/Memory Router.md" in instructions
            assert "Agent/Memory/index.md" not in instructions

            install_agent_memory(duplicate_project_root, duplicate_agent_path, duplicate_instruction_path)
            assert memory_router_path(duplicate_agent_path).exists()
            assert not (duplicate_agent_path / "Memory" / "index.md").exists()

            try:
                install_agent_memory(conflict_project_root, conflict_agent_path, conflict_instruction_path)
            except RuntimeError as exc:
                assert "different content" in str(exc)
            else:
                raise AssertionError("conflicting router and index files were accepted")
        finally:
            if previous_root is None:
                os.environ.pop("AGENT_MEMORY_ROOT", None)
            else:
                os.environ["AGENT_MEMORY_ROOT"] = previous_root
    return 0


def find_section_start(lines: list[str], title: str) -> int | None:
    marker = f"## {title}"
    for i, line in enumerate(lines):
        if line == marker:
            return i
    return None


def find_next_section(lines: list[str], start: int) -> int:
    for i in range(start + 1, len(lines)):
        if lines[i].startswith("## "):
            return i
    return len(lines)


def ensure_section(text: str, title: str) -> str:
    marker = f"## {title}"
    if marker in text:
        return text
    suffix = "" if text.endswith("\n") else "\n"
    return f"{text}{suffix}\n{marker}\n\n"


def ensure_before_project_work_item(text: str, line: str) -> str:
    if line in text:
        return text
    lines = text.splitlines()
    for i, current in enumerate(lines):
        if current.strip() == "- Before project work, read:":
            lines.insert(i + 1, line)
            return "\n".join(lines) + "\n"
    return ensure_section_bullet(
        text,
        "Context and precedence",
        f"- Before project work, read:\n{line}",
    )


def ensure_section_bullet(text: str, title: str, bullet: str) -> str:
    if bullet in text:
        return text
    marker = f"## {title}"
    start = text.index(marker)
    next_section = text.find("\n## ", start + len(marker))
    insert_at = len(text) if next_section == -1 else next_section
    before = text[:insert_at].rstrip()
    after = text[insert_at:]
    return f"{before}\n\n{bullet}\n{after}"


if __name__ == "__main__":
    raise SystemExit(main())
