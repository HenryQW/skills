# Distill Reference

Distill turns `.context/decisions.jsonl` durable candidates into staged Agent notes. Prefer the structured JSONL source; use `.context/progress.md` only to clarify an already durable decision.

For the current Agent structure:

- Approved router: `Agent/Memory/index.md`.
- Approved notes: `Agent/Memory/Decisions/` and `Agent/Memory/Guidance/`.
- Staging only: `Agent/Memory/Decisions/Inbox/` and `Agent/Memory/Guidance/Inbox/`.
- Do not create Inbox `index.md` files.
- Do not move staged notes into approved folders or add them to `Agent/Memory/index.md` unless explicitly approved.
- A topic slug maps directly to `<folder>/<topic-slug>.md`; never search note bodies to choose a destination.
- Preview writes exact rendered bytes and state hashes to `.context/memory-distill-preview.json`.
- Apply with `--apply` writes that artifact byte-for-byte and rejects source or staged-note drift.

## Write Memory For

- accepted decisions and why they exist
- root causes future agents might rediscover
- repeated repo/worktree traps
- mistakes to avoid
- rules and coding style
- library or framework preferences
- non-obvious commands or validation paths
- architecture context that survived review or merge readiness

## Do Not Write Memory For

- PR summary or one-note-per-PR archives
- ordinary todo progress
- files changed
- tests passed
- transient branch state
- passing/failing checks with no reusable lesson
- one-off typos or mistakes
- duplicate context already present in `Agent/Memory/Decisions/` or `Agent/Memory/Guidance/`

## Memory Shape

Use the project convention if one exists. Otherwise:

```md
---
type: project-note
created: 'YYYY-MM-DD'
last_updated: 'YYYY-MM-DD'
tags: []
---
# Title

## Date

YYYY-MM-DD.

## Decision

- **Durable decision.** Reason: why. Source: source.

## Sources

- source note, issue, PR, or spec
```
