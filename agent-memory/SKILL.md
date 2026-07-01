---
name: agent-memory
description: Set up and use project-scoped agent memory with `.context/progress.md`, `.gitignore`, repo instructions, and Obsidian `projects/.../Agent/Memory`. Use when the user invokes `$agent-memory`, asks to set up agent memory, project memory, progress tracking, `.context/progress.md`, Obsidian Agent memory, or asks to distill progress.
---

# Agent Memory

## Overview

Maintain the smallest durable memory loop:

- `.context/progress.md` is the local, ignored task ledger.
- `AGENTS.md` tells agents how to use progress and Obsidian Agent memory.
- `${OBSIDIAN_VAULT_PATH}/projects/.../Agent/Memory` stores durable cross-worktree context.

## Setup Mode

Use setup mode when a project needs this system installed or checked.

1. Resolve the project Obsidian `Agent/` folder. Prefer an explicit user path; otherwise infer it from `AGENTS.md` or project docs. If ambiguous, ask.
2. From this skill folder, run:

```bash
python3 scripts/setup_agent_memory.py \
  --project-root /path/to/project \
  --agent-path "$OBSIDIAN_VAULT_PATH/projects/<Project>/.../Agent"
```

3. Review the diff against `references/setup.md`.

Reference: `references/setup.md`.
Canonical `AGENTS.md` snippets: `references/agents.md`.

## Distill Mode

Use distill mode when the user invokes `$agent-memory` for distillation or asks to distill progress.

1. Read `.context/progress.md`.
2. Read the project `Agent/Memory/index.md`.
3. Follow `references/distill.md`.

Reference: `references/distill.md`.
