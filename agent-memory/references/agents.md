# AGENTS.md Memory Snippets

Setup uses these exact snippets. Keep placeholders intact; the setup script replaces them.

## Context and precedence item

```md
  - `{memory_router_ref}`
```

## Execution item

```md
- Use `.context/progress.md` for transient task state, `.context/decisions.jsonl` for durable decision candidates, and `.context/memory-context.md` for generated memory context. Before non-trivial work, read `{memory_router_ref}`, then load only matching approved notes from `{memory_dir_ref}/Decisions/` or `{memory_dir_ref}/Guidance/`; never load Inbox during normal context loading. When `$agent-memory` is invoked or progress distillation is requested, prefer the agent-memory scripts: `memory_context.py` to load matching approved notes, `append_decision.py` to record durable decisions, and `distill_memory.py --verify` to stage durable candidates under `{memory_dir_ref}/Decisions/Inbox/` or `{memory_dir_ref}/Guidance/Inbox/` for human review. Do not promote Inbox notes or edit the router unless explicitly approved. Skip routine progress, duplicate lessons, one-off mistakes, and one-note-per-PR archives.
```
