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
- During work, capture every distinct durable decision and guidance item; do not
  stop after the first candidate or combine unrelated topics.
- A decision settles a non-obvious engineering choice. It qualifies when the
  user states it or approves a plan, design, or implementation containing it.
  Record its rationale, material alternatives or tradeoffs, and expected impact.
- Guidance preserves a verified repository improvement future sessions should
  repeat or protect. Record what changed, when the practice applies, why it is
  better than the previous behavior, and what future sessions must watch. User
  corrections, repository invariants, and reusable failure lessons also qualify.
- Capturing a candidate does not authorize final `--apply`.
- Skip routine progress, bare file or commit summaries, checks, transient state,
  code-obvious mechanics, reversible local choices, and duplicates.
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

Append one decision candidate per choice:

```bash
python3 <agent_memory_dir>/scripts/append_decision.py --project-root /path/to/project --topic order-processing --decision "Keep retry policy in the application service" --reason "All transports share one policy." --alternatives "Per-adapter retries would diverge." --impact "Every transport now uses one policy." --source "approved architecture plan"
```

Append one guidance candidate per reusable practice:

```bash
python3 <agent_memory_dir>/scripts/append_decision.py --project-root /path/to/project --topic order-processing --guidance "Keep retry policy changes in the application service." --applies-when "Adding or changing an order transport." --change "Retry policy moved from adapters into the shared application service." --improvement "Transport behavior can no longer drift." --attention "Future sessions must keep transport adapters policy-free." --file src/orders/service.py --source "verified implementation"
```

Equivalent normalized candidates receive the same stable ID and are recorded
once. Before the final preview, scan the accepted choices, repository delta,
user corrections, reusable failures, and `.context/progress.md` for missed
durable candidates. The ledger may confirm a candidate but is not itself memory.
Then preview with:

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
