---
name: agent-memory
description: Use project-scoped agent memory with `.context/progress.md` and markdown files under `OBSIDIAN_PROJECT`. Use when the user or another workflow invokes `$agent-memory load`, `$agent-memory distill`, or `$agent-memory --setup`.
---

# Agent Memory

Memory is artifact-driven: `.context/progress.md` is the task ledger;
`.context/decisions.jsonl` stores durable candidates; generated load and preview
artifacts remain under `.context/`. The project `AGENTS.md` declares
`OBSIDIAN_PROJECT`; `Agent/Memory/index.md` links approved `Decisions/` and
`Guidance/` notes. Their `Inbox/` folders are staging only.

Only `--setup` reads `references/setup.md` or runs setup.

## Boundary

- `$agent-memory load` runs at a top-level workflow entry. Missing configuration
  or matching topics returns `memory_load=SKIPPED` and does not stop the caller.
- During work, capture only accepted decisions, reusable root causes, repository
  traps or rules, non-obvious commands, and reviewed architecture context. Skip
  routine progress, files changed, checks, transient state, and duplicates.
- `$agent-memory distill` runs before a top-level `Done`, `Stop`, or `Blocked`.
  Nested skills preserve `.context/decisions.jsonl` for their caller.
- Memory failure never replaces or hides the caller's terminal result.

## Load

Select at most two exact linked topic slugs, then run:

```bash
python3 <agent_memory_dir>/scripts/memory_context.py --project-root /path/to/project --topic <topic-id> --out .context/memory-context.md
```

Read the 6,000-character-capped output only when notes loaded.

## Capture and Distill

Append a durable candidate with:

```bash
python3 <agent_memory_dir>/scripts/append_decision.py --project-root /path/to/project --topic issue-workbench --decision "Single known issues use issue-workbench directly" --reason "Avoid parent graph overhead" --source "issue #123"
```

Equivalent normalized decisions receive the same stable ID and are recorded once.
Preview before final handoff or when requested:

```bash
python3 <agent_memory_dir>/scripts/distill_memory.py --project-root /path/to/project --source .context/decisions.jsonl
```

Inspect `.context/memory-distill-preview.json`; only explicit approval authorizes
applying its exact rendered bytes:

```bash
python3 <agent_memory_dir>/scripts/distill_memory.py --project-root /path/to/project --source .context/decisions.jsonl --apply
```

Apply rejects source or staged-note drift. Do not promote Inbox notes, create
Inbox indexes, or edit `Agent/Memory/index.md` without explicit approval. Topic
slugs map directly to staged filenames; never search note bodies to choose a
destination. Use `.context/progress.md` only to clarify an already durable
decision. No durable records returns `memory_write=SKIPPED` without asking.
