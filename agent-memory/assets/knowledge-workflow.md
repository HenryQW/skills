# Knowledge Workflow

Use only when the project `AGENTS.md` defines `OBSIDIAN_PROJECT`. Never infer a project memory path.

## Load

- Start from `${OBSIDIAN_PROJECT}/Agent/Memory/index.md`.
- Follow only task-relevant links to approved notes.
- Never load notes from `Decisions/Inbox/` or `Guidance/Inbox/` during normal work.
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

Record only durable information future agents would otherwise rediscover. Skip routine progress, debugging steps, code-obvious facts, and conversation summaries.

- Decisions: date, decision, reason, alternatives, and impact.
- Guidance: when it applies and what to do.
- Stage new notes in `Decisions/Inbox/<topic-slug>.md` or `Guidance/Inbox/<topic-slug>.md`.
- Do not create Inbox indexes, promote staged notes, or link them from the router without explicit approval.
- If no durable information was created, do not update memory.
