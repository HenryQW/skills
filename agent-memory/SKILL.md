---
name: agent-memory
description: Use project-scoped agent memory with `.context/progress.md` and markdown files under `OBSIDIAN_PROJECT`. Use when the user or another workflow invokes `$agent-memory load`, `$agent-memory distill`, or `$agent-memory --setup`.
---

# Agent Memory

## Overview

Memory is artifact-driven: `.context/progress.md` is the local task ledger; `.context/decisions.jsonl` records durable candidates; `memory-context.md` and `memory-distill-preview.json` are generated load and preview artifacts. The project `AGENTS.md` declares `OBSIDIAN_PROJECT`; its `Agent/Memory/index.md` is the approved router. `Decisions/` and `Guidance/` are approved notes; their `Inbox/` folders are staging only. Do not promote or link staged notes without explicit approval, or create one note per PR.

## Setup Gate

Only when the invocation includes `--setup`, read and follow `references/setup.md`. Otherwise, do not read that reference or run setup.

## Workflow Boundary

- `$agent-memory load`: at a top-level workflow entry, load exact approved topics relevant to the task. If memory is not configured or no topic matches, return `memory_load=SKIPPED` and continue.
- During the workflow, append only durable decision candidates.
- `$agent-memory distill`: follow the Distill procedure before a top-level workflow returns `Done`, `Stop`, or `Blocked`. If there are no new durable records, return `memory_write=SKIPPED` without asking.
- Nested skills do not distill. They preserve `.context/decisions.jsonl` for the top-level caller.
- Memory failure must not replace or hide the caller's terminal result.

## Context Load

For `$agent-memory load`, select at most two exact topic IDs from the approved index, then run:

```bash
python3 <agent_memory_dir>/scripts/memory_context.py --project-root /path/to/project --topic <topic-id> --out .context/memory-context.md
```

The topic ID is the unique lowercase filename slug linked from the index. The generated file is capped at 6,000 characters; read it only when notes loaded.

## Decision Capture

When a durable decision is made, append a structured local candidate:

```bash
python3 <agent_memory_dir>/scripts/append_decision.py --project-root /path/to/project --topic issue-workbench --decision "Single known issues use issue-workbench directly" --reason "Avoid parent graph overhead" --source "issue #123"
```

Skip routine progress, checks, and implementation details.
Equivalent normalized decisions receive the same stable ID and are recorded once.

## Distill

Preview distillation before final PR handoff or when explicitly requested:

```bash
python3 <agent_memory_dir>/scripts/distill_memory.py --project-root /path/to/project --source .context/decisions.jsonl
```

Inspect `.context/memory-distill-preview.json`, then apply its exact rendered bytes only after explicit approval:

```bash
python3 <agent_memory_dir>/scripts/distill_memory.py --project-root /path/to/project --source .context/decisions.jsonl --apply
```

Apply rejects source or staged-note drift. Do not promote Inbox notes or edit `Agent/Memory/index.md` without explicit approval. Use `.context/progress.md` only to clarify already durable decisions; follow `references/distill.md` for qualification and staging details.
