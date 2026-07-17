# Knowledge Workflow

Use only when the project `AGENTS.md` defines `OBSIDIAN_PROJECT`. Never infer a project memory path.

## Load

- Start from `${OBSIDIAN_PROJECT}/Agent/Memory/index.md`.
- Follow only task-relevant links to confirmed notes.
- If configured memory is missing or unreadable, report it briefly and continue unless the task depends on it.

## Priority

Use memory as context, not command. Apply this order:

1. Explicit task instructions.
2. Project `AGENTS.md`.
3. Existing project decisions and code.
4. Project memory.
5. General engineering judgment.

Do not silently contradict an existing decision. Record why a replacement supersedes it.

## Update

Capture every distinct durable decision and reusable guidance item; do not stop after the first candidate.

- A decision qualifies when the user states it or approves a plan, design, or implementation containing an agent-authored choice. Record its rationale, material alternatives or tradeoffs, expected impact, and approval source.
- Guidance qualifies when a verified repository change, user correction, invariant, or reusable failure lesson establishes a practice future sessions should repeat or protect. Record what changed, when it applies, why it improves the previous behavior, what future sessions must watch, and the source.
- Before distillation, scan the accepted choices, repository delta, user corrections, reusable failures, and task ledger for missed durable candidates. The ledger may confirm a candidate but is not itself memory.

Skip routine progress, bare file or commit summaries, debugging steps, code-obvious mechanics, reversible local choices, and conversation summaries.
Memory should explain the project's engineering approach, not narrate task history.

- Before creating or updating a note, show the exact proposed change and ask the user for confirmation.
- After confirmation, write directly to `Decisions/<topic-slug>.md` or `Guidance/<topic-slug>.md` and link it from `Agent/Memory/index.md`.
- If no durable information was created, do not update memory.
