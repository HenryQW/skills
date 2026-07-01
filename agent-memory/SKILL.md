---
name: agent-memory
description: Set up and use project-scoped agent memory with `.context/progress.md`, `.gitignore`, repo instructions, and markdown files under `AGENT_MEMORY_ROOT`. Use when the user invokes `$agent-memory`, asks to set up agent memory, project memory, progress tracking, `.context/progress.md`, markdown Agent memory, or asks to distill progress.
---

# Agent Memory

## Overview

Maintain the smallest durable memory loop:

- `.context/progress.md` is the local, ignored task ledger.
- `AGENTS.md` tells agents how to use progress and markdown Agent memory.
- `${AGENT_MEMORY_ROOT}/projects/.../Agent/Memory` stores durable cross-worktree context.

## Setup Mode

Use setup mode when a project needs this system installed or checked.

1. Resolve the project markdown `Agent/` folder under `AGENT_MEMORY_ROOT`. If ambiguous, ask.
2. Set `AGENT_MEMORY_ROOT` to the markdown root for this shell session.
3. From this skill folder, run:

```bash
export AGENT_MEMORY_ROOT="/path/to/markdown-root"
python3 scripts/setup_agent_memory.py \
  --project-root /path/to/project \
  --agent-path "$AGENT_MEMORY_ROOT/projects/<Project>/.../Agent"
```

4. Review the diff against `references/setup.md`.

Reference: `references/setup.md`.
Canonical `AGENTS.md` snippets: `references/agents.md`.

## Distill Mode

Use distill mode when the user invokes `$agent-memory` for distillation or asks to distill progress.

1. Read `.context/progress.md`.
2. Read the project `Agent/Memory/index.md`.
3. Follow `references/distill.md`.

Reference: `references/distill.md`.
