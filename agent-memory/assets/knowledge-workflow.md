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

Record durable engineering decisions whose rationale future agents would otherwise rediscover, including why code is shaped a certain way, why architecture boundaries exist, and why optimizations or tradeoffs were chosen. A decision qualifies when the user states it or approves a plan, design, or implementation containing an agent-authored choice. It does not need to originate in user wording.

Skip routine progress, debugging steps, code-obvious mechanics, reversible local choices, and conversation summaries.
Memory should explain the project's engineering approach, not narrate task history.

- Decisions: date, decision, reason, material alternatives or tradeoffs, impact, and approval source.
- Guidance: when it applies and what to do.
- Before creating or updating a note, show the exact proposed change and ask the user for confirmation.
- After confirmation, write directly to `Decisions/<topic-slug>.md` or `Guidance/<topic-slug>.md` and link it from `Agent/Memory/index.md`.
- If no durable information was created, do not update memory.
