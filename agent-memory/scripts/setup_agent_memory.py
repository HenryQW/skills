#!/usr/bin/env python3
"""Install project agent-memory plumbing."""

from __future__ import annotations

import argparse
import os
import tempfile
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[1]
AGENTS_SNIPPETS = SKILL_ROOT / "references" / "agents.md"
INDEX_FILENAME = "index.md"
LEGACY_MEMORY_ROUTER_FILENAME = "Memory Router.md"

PROGRESS_TEMPLATE = """# Progress

No active task.

Use this file as the local task ledger during implementation.

## Notes

- Keep this file local. Distill durable context with `$agent-memory` when requested.
"""

IGNORED_CONTEXT_FILES = (
    ".context/progress.md",
    ".context/decisions.jsonl",
    ".context/memory-context.md",
)


AGENT_INDEX_TEMPLATE = """---
type: project-note
status: active
tags: []
---
# Agent

**Summary**: Lean router for approved project agent decisions and reusable guidance.

---

## Role

Single router for approved project agent decisions and guidance.

## Loading Rule

Read this index before non-trivial project work. Load only the specific approved decision or guidance note whose title or summary matches the task. Do not load the full library by default. Do not read `Decisions/Inbox/` or `Guidance/Inbox/` during normal context loading; use Inbox only to create, review, or explicitly promote staged notes.

Priority for conflicts: explicit task instructions, project `AGENTS.md`, decisions, guidance, global principles, then general judgment.

When `$agent-memory` is invoked or progress distillation is requested, extract durable context into a new note under `Decisions/Inbox/<slug>.md` or `Guidance/Inbox/<slug>.md` using the same final note format. Treat Inbox folders as staging for human review. Do not create Inbox `index.md` files. Do not move staged notes into production folders or add them to this router unless explicitly approved. Do not preserve routine progress.

## Decisions

## Guidance
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
    existing = set(text.splitlines())
    missing = [item for item in IGNORED_CONTEXT_FILES if item not in existing]
    if not missing:
        return
    suffix = "" if not text or text.endswith("\n") else "\n"
    block = "\n# Agent local context\n" + "\n".join(missing) + "\n"
    gitignore.write_text(text + suffix + block, encoding="utf-8")


def memory_router_path(agent_path: Path) -> Path:
    return agent_path / INDEX_FILENAME


def legacy_memory_router_path(agent_path: Path) -> Path:
    return agent_path / "Memory" / LEGACY_MEMORY_ROUTER_FILENAME


def ensure_memory_router(agent_path: Path) -> None:
    agent_path.mkdir(parents=True, exist_ok=True)
    (agent_path / "Decisions" / "Inbox").mkdir(parents=True, exist_ok=True)
    (agent_path / "Guidance" / "Inbox").mkdir(parents=True, exist_ok=True)
    index = memory_router_path(agent_path)
    legacy = legacy_memory_router_path(agent_path)
    if not index.exists() and legacy.exists():
        index.write_text(migrate_legacy_index(legacy.read_text(encoding="utf-8")), encoding="utf-8")
        return
    if not index.exists():
        index.write_text(AGENT_INDEX_TEMPLATE, encoding="utf-8")


def migrate_legacy_index(text: str) -> str:
    text = text.replace("# Memory Router", "# Agent", 1)
    text = text.replace("# Agent Memory", "# Agent", 1)
    text = text.replace("Read this router", "Read this index", 1)
    text = text.replace("## Memory", "## Guidance", 1)
    return text


def ensure_agents(path: Path, memory_router_ref: str, agent_path: Path) -> None:
    text = path.read_text(encoding="utf-8") if path.exists() else "# AGENTS.md\n"
    text = ensure_section(text, "Context and precedence")
    text = ensure_section(text, "Execution")

    snippets = load_agents_snippets(memory_router_ref, memory_ref(agent_path))
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
                "/Agent/index.md`" in line
                or "/Agent/Memory/index.md`" in line
                or f"/Agent/Memory/{LEGACY_MEMORY_ROUTER_FILENAME}`" in line
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
        fresh_agent_path = memory_root / "projects" / "Fresh" / "Platform" / "Agent"
        fresh_instruction_path = fresh_project_root / "AGENTS.md"
        legacy_project_root = tmp / "legacy-repo"
        legacy_agent_path = memory_root / "projects" / "Example" / "Agent"
        legacy_memory_dir = legacy_agent_path / "Memory"
        legacy_instruction_path = legacy_project_root / "AGENTS.md"
        fresh_project_root.mkdir()
        legacy_project_root.mkdir()
        legacy_memory_dir.mkdir(parents=True)
        old_router = (
            "# Memory Router\n\n"
            "Summary: Durable context for future agents.\n\n"
            "## Loading Rule\n\n"
            "Read this router before non-trivial project work.\n\n"
            "## Memory\n\n"
            "- Existing note.\n"
        )
        legacy_memory_router_path(legacy_agent_path).write_text(old_router, encoding="utf-8")
        legacy_instruction_path.write_text(
            "# AGENTS.md\n\n"
            "## Context and precedence\n\n"
            "- Before project work, read:\n"
            "  - `${AGENT_MEMORY_ROOT}/projects/Example/Agent/Memory/Memory Router.md`\n",
            encoding="utf-8",
        )

        try:
            os.environ["AGENT_MEMORY_ROOT"] = os.fspath(memory_root)
            install_agent_memory(fresh_project_root, fresh_agent_path, fresh_instruction_path)

            assert (fresh_project_root / ".context" / "progress.md").exists()
            fresh_gitignore = (fresh_project_root / ".gitignore").read_text(encoding="utf-8")
            assert ".context/progress.md" in fresh_gitignore
            assert ".context/decisions.jsonl" in fresh_gitignore
            assert ".context/memory-context.md" in fresh_gitignore
            assert memory_router_path(fresh_agent_path).exists()
            assert (fresh_agent_path / "Decisions" / "Inbox").is_dir()
            assert (fresh_agent_path / "Guidance" / "Inbox").is_dir()
            fresh_router_text = memory_router_path(fresh_agent_path).read_text(encoding="utf-8")
            assert fresh_router_text.startswith("---")
            assert "# Agent" in fresh_router_text
            assert "Read this index" in fresh_router_text
            assert "Decisions/Inbox" in fresh_router_text

            instructions = fresh_instruction_path.read_text(encoding="utf-8")
            assert "Agent/index.md" in instructions
            assert "Agent/Memory/Memory Router.md" not in instructions
            assert "Decisions/Inbox" in instructions

            install_agent_memory(legacy_project_root, legacy_agent_path, legacy_instruction_path)
            assert memory_router_path(legacy_agent_path).exists()
            legacy_router_text = memory_router_path(legacy_agent_path).read_text(encoding="utf-8")
            assert legacy_router_text.startswith("# Agent")
            assert "Read this index" in legacy_router_text
            assert "Existing note" in legacy_router_text
            instructions = legacy_instruction_path.read_text(encoding="utf-8")
            assert "Agent/index.md" in instructions
            assert "Agent/Memory/Memory Router.md" not in instructions
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
