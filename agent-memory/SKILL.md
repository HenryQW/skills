---
name: agent-memory
description: Use project-scoped agent memory with `.context/progress.md` and markdown files under `OBSIDIAN_PROJECT`. Use when the user or another workflow invokes `$agent-memory load`, `$agent-memory distill`, or `$agent-memory --setup`.
---

# Agent Memory

## Overview

Maintain the smallest durable memory loop:

- `.context/progress.md` is the local, ignored task ledger.
- `.context/decisions.jsonl` is the local, ignored durable-decision candidate log.
- `.context/memory-context.md` is generated task context loaded from matching memory notes.
- `.context/memory-distill-preview.json` stores ignored rendered bytes and state hashes between distillation preview and apply.
- The project `AGENTS.md` declares `OBSIDIAN_PROJECT=${OBSIDIAN_ROOT}/<project-path>` and supplies only project-specific instructions.
- `${OBSIDIAN_PROJECT}/Agent/Memory/index.md` is the approved project memory router.
- `${OBSIDIAN_PROJECT}/Agent/Memory/Decisions/` and `Guidance/` store approved notes.
- `Decisions/Inbox/` and `Guidance/Inbox/` are staging only; agents create there but do not promote or link staged notes without explicit approval.

Memory is artifact-driven, not conversation-driven: append structured decision candidates during work, then let scripts conservatively patch topic notes. Do not create one note per PR.

## Setup Gate

Only when the invocation includes `--setup`, read and follow `references/setup.md`. Otherwise, do not read that reference or run setup.

## Workflow Boundary

- `$agent-memory load`: at a top-level workflow entry, load exact approved topics relevant to the task. If memory is not configured or no topic matches, return `memory_load=SKIPPED` and continue.
- While the workflow runs, append only durable decision candidates as described below.
- `$agent-memory distill`: follow the Distill procedure before a top-level workflow returns `Done`, `Stop`, or `Blocked`. If there are no new durable records, return `memory_write=SKIPPED` without asking.
- Nested skills do not distill. They preserve `.context/decisions.jsonl` for the top-level caller.
- Memory failure must not replace or hide the caller's terminal result.

## Context Load

For `$agent-memory load`, select at most two exact topic IDs from the approved memory index, then run:

```bash
python3 <agent_memory_dir>/scripts/memory_context.py --project-root /path/to/project --topic <topic-id> --out .context/memory-context.md
```

The topic ID is the lowercase slug of an approved note filename linked from `Agent/Memory/index.md` and must be unique across Decisions and Guidance. The generated file is capped at 6,000 characters. Read it only when notes were loaded.

## Decision Capture

When a durable decision is made, append a structured local candidate:

```bash
python3 <agent_memory_dir>/scripts/append_decision.py \
  --project-root /path/to/project \
  --topic issue-workbench \
  --decision "Single known issues use issue-workbench directly" \
  --reason "Avoid parent graph overhead for one actionable issue" \
  --source "issue #123"
```

Skip routine progress, checks, and implementation details.
Equivalent normalized decisions receive the same stable ID and are recorded once.

## Distill

Preview conservative distillation before final PR handoff or when explicitly requested:

```bash
python3 <agent_memory_dir>/scripts/distill_memory.py --project-root /path/to/project --source .context/decisions.jsonl
```

Inspect `.context/memory-distill-preview.json`, then apply those exact rendered bytes only after approval:

```bash
python3 <agent_memory_dir>/scripts/distill_memory.py --project-root /path/to/project --source .context/decisions.jsonl --apply
```

Topic slugs map directly to staged filenames under `Agent/Memory/Decisions/Inbox/` or `Agent/Memory/Guidance/Inbox/`; note bodies are never searched to choose a target. Apply rejects source or staged-note drift after preview. The command must not create one note per PR, promote Inbox notes, or edit `Agent/Memory/index.md` unless explicitly approved.
Use `.context/progress.md` only to clarify already durable decisions. Follow `references/distill.md` for what qualifies.
