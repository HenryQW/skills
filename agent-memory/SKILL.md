---
name: agent-memory
description: Set up and use project-scoped agent memory with `.context/progress.md`, `.gitignore`, repo instructions, and markdown files under `AGENT_MEMORY_ROOT`. Use when the user invokes `$agent-memory`, asks to set up agent memory, project memory, progress tracking, `.context/progress.md`, markdown Agent memory, or asks to distill progress.
---

# Agent Memory

## Overview

Maintain the smallest durable memory loop:

- `.context/progress.md` is the local, ignored task ledger.
- `.context/decisions.jsonl` is the local, ignored durable-decision candidate log.
- `.context/memory-context.md` is generated task context loaded from matching memory notes.
- `AGENTS.md` tells agents how to use progress and markdown Agent memory.
- `${AGENT_MEMORY_ROOT}/projects/.../Agent/index.md` is the approved project router.
- `${AGENT_MEMORY_ROOT}/projects/.../Agent/Decisions/` and `Guidance/` store approved notes.
- `Decisions/Inbox/` and `Guidance/Inbox/` are staging only; agents create there but do not promote or link staged notes without explicit approval.

Memory is artifact-driven, not conversation-driven: append structured decision candidates during work, then let scripts conservatively patch topic notes. Do not create one note per PR.

## Setup

Use setup when a project needs this system installed or checked.

1. Resolve the project markdown `Agent/` folder under `AGENT_MEMORY_ROOT`. If ambiguous, ask. Example: `${AGENT_MEMORY_ROOT}/projects/Evermark/Platform/Agent`.
2. Set `AGENT_MEMORY_ROOT` to the markdown root for this shell session.
3. From this skill folder, run:

```bash
export AGENT_MEMORY_ROOT="/path/to/markdown-root"
python3 scripts/setup_agent_memory.py \
  --project-root /path/to/project \
  --agent-path "$AGENT_MEMORY_ROOT/projects/<Project>/.../Agent"
```

4. Review the diff against `references/setup.md`.

Reference: `references/setup.md`.
Canonical `AGENTS.md` snippets: `references/agents.md`.

## Context Load

Use deterministic context load at the start of non-trivial implementation when memory is configured:

```bash
python3 scripts/memory_context.py --project-root /path/to/project --agent-path "$AGENT_MEMORY_ROOT/projects/<Project>/.../Agent" --issue <issue_number> --out .context/memory-context.md
```

Read `.context/memory-context.md` only if matching notes were loaded.

## Decision Capture

When a durable decision is made, append a structured local candidate:

```bash
python3 scripts/append_decision.py \
  --project-root /path/to/project \
  --topic issue-workbench \
  --decision "Single known issues use issue-workbench directly" \
  --reason "Avoid parent graph overhead for one actionable issue" \
  --source "issue #123"
```

Skip routine progress, checks, and implementation details.

## Distill

Use conservative distillation before final PR handoff or when explicitly requested:

```bash
python3 scripts/distill_memory.py --project-root /path/to/project --agent-path "$AGENT_MEMORY_ROOT/projects/<Project>/.../Agent" --source .context/decisions.jsonl --verify
```

The command either prints `memory_write=SKIPPED ...` or writes staged notes under `Agent/Decisions/Inbox/` or `Agent/Guidance/Inbox/`. It must not create one note per PR, promote Inbox notes, or edit `Agent/index.md` unless explicitly approved.

## Distill On Request

When the user invokes `$agent-memory` for distillation or asks to distill progress, run:

```bash
python3 scripts/distill_memory.py --project-root /path/to/project --agent-path "$AGENT_MEMORY_ROOT/projects/<Project>/.../Agent" --source .context/decisions.jsonl --verify
```

Use `.context/progress.md` only to clarify already durable decisions. Follow `references/distill.md` for what qualifies.

Reference: `references/distill.md`.
