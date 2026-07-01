#!/usr/bin/env python3
"""Install project agent-memory plumbing."""

from __future__ import annotations

import argparse
import os
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[1]
AGENTS_SNIPPETS = SKILL_ROOT / "references" / "agents.md"

PROGRESS_TEMPLATE = """# Progress

No active task.

Use this file as the local task ledger during implementation.

## Notes

- Keep this file local. Distill durable context with `$agent-memory` when requested.
"""


MEMORY_INDEX_TEMPLATE = """# Agent Memory

Summary: Durable context for future agents. Load only matching notes; do not load this full folder by default.
Keywords: agent memory, guidance, mistakes, preferences

## Loading Rule

Read this index before non-trivial project work, then open only the memory notes whose title, summary, or keywords match the task.

Memory notes can include history, mistakes to avoid, rules, coding style, library preferences, and validation paths.

When `$agent-memory` is invoked or progress distillation is requested, agents should distill `.context/progress.md` into a real memory note only when it contains durable context future agents would otherwise rediscover. No memory should be written for routine progress.

## Memory

No active memory yet.
"""


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", default=".")
    parser.add_argument("--agent-path", required=True)
    parser.add_argument("--instruction-file", default="AGENTS.md")
    args = parser.parse_args()

    project_root = Path(args.project_root).resolve()
    memory_root = parse_memory_root(parser)
    agent_path = Path(os.path.expandvars(args.agent_path)).resolve()
    require_under_memory_root(parser, agent_path, memory_root)
    instruction_path = project_root / args.instruction_file

    memory_index_ref = memory_ref(agent_path / "Memory" / "index.md")

    ensure_progress(project_root)
    ensure_gitignore(project_root)
    ensure_memory_index(agent_path)
    ensure_agents(instruction_path, memory_index_ref, agent_path)

    print("project agent memory setup complete")
    return 0


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


def ensure_memory_index(agent_path: Path) -> None:
    memory = agent_path / "Memory"
    memory.mkdir(parents=True, exist_ok=True)
    index = memory / "index.md"
    if not index.exists():
        index.write_text(MEMORY_INDEX_TEMPLATE, encoding="utf-8")


def ensure_agents(path: Path, memory_index_ref: str, agent_path: Path) -> None:
    text = path.read_text(encoding="utf-8") if path.exists() else "# AGENTS.md\n"
    text = ensure_section(text, "Context and precedence")
    text = ensure_section(text, "Execution")

    snippets = load_agents_snippets(memory_index_ref, memory_ref(agent_path / "Memory"))
    text = remove_generated_memory_lines(text)
    context_line = snippets["Context and precedence item"]
    text = ensure_before_project_work_item(text, context_line)

    text = ensure_section_bullet(text, "Execution", snippets["Execution item"])

    path.write_text(text, encoding="utf-8")


def load_agents_snippets(memory_index_ref: str, memory_dir_ref: str) -> dict[str, str]:
    text = AGENTS_SNIPPETS.read_text(encoding="utf-8")
    snippets = {
        "Context and precedence item": extract_fenced_block(text, "Context and precedence item"),
        "Execution item": extract_fenced_block(text, "Execution item"),
    }
    return {
        key: value.format(
            memory_index_ref=memory_index_ref,
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
        generated_context = in_context and line.strip().startswith("- `") and "/Agent/Memory/index.md`" in line
        if not (generated_execution or generated_context):
            kept.append(line)
    return "\n".join(kept) + "\n"


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
