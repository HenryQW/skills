---
name: agent-memory
description: Use project-scoped agent memory with `.context/progress.md` and markdown files under `OBSIDIAN_PROJECT`. Use when the user or another workflow invokes `$agent-memory load`, `$agent-memory distill`, or `$agent-memory --setup`.
---

# Agent Memory

Memory is artifact-driven: `.context/progress.md` is the task ledger;
`.context/decisions.jsonl` stores durable candidates; generated load and preview
artifacts remain under `.context/`. The project `AGENTS.md` declares
`OBSIDIAN_PROJECT`; `Agent/Memory/index.md` links approved `Decisions/` and
`Guidance/` notes. Confirmed notes are written there directly.

Only `--setup` reads `references/setup.md` or runs setup.

## Boundary

- `$agent-memory load` runs at a top-level workflow entry. Missing configuration
  or matching topics returns `memory_load=SKIPPED` and does not stop the caller.
- During work, capture accepted, non-obvious engineering decisions whose
  rationale future agents would otherwise rediscover: why code is shaped a
  certain way, why an architecture boundary exists, why an optimization or
  tradeoff was chosen, plus reusable root causes and repository rules.
- A decision is accepted when the user states it or approves a plan, design, or
  implementation containing an agent-authored choice. Record why it was chosen,
  material alternatives or tradeoffs, and expected impact. This qualifies the
  decision for capture but does not authorize final `--apply`.
- Skip routine progress, files changed, checks, transient state, code-obvious
  mechanics, reversible local choices, and duplicates.
- Memory should explain the project's engineering approach, not narrate task
  history.
- `$agent-memory distill` runs only when the top-level workflow is otherwise
  ready to return final `Done`, `Stop`, or `Blocked`. Resumable `PENDING` or
  `PENDING_REVIEW`, approval waits, handoffs, and nested skills preserve
  `.context/decisions.jsonl` without preview or apply.
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
python3 <agent_memory_dir>/scripts/append_decision.py --project-root /path/to/project --topic order-processing --decision "Keep retry policy in the application service" --reason "All transports share one policy; centralizing it avoids divergent behavior. Rejected per-adapter retries." --source "approved architecture plan"
```

Equivalent normalized decisions receive the same stable ID and are recorded once.
At the final top-level boundary, preview with:

```bash
python3 <agent_memory_dir>/scripts/distill_memory.py --project-root /path/to/project --source .context/decisions.jsonl
```

Inspect `.context/memory-distill-preview.json`; only explicit approval authorizes
creating or updating its exact final notes and index links:

```bash
python3 <agent_memory_dir>/scripts/distill_memory.py --project-root /path/to/project --source .context/decisions.jsonl --apply
```

Apply rejects source or destination drift, writes directly to `Decisions/` or
`Guidance/`, and adds missing links to `Agent/Memory/index.md`. Do not apply
before the user confirms the preview. Topic slugs map directly to final
filenames; never search note bodies to choose a destination. Use
`.context/progress.md` only to clarify an already durable decision. No durable
records returns `memory_write=SKIPPED` without asking.
