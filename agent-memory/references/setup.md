# Setup Reference

Setup mode installs deterministic project plumbing. Keep edits minimal and idempotent.

## Required Inputs

- repo root
- `AGENT_MEMORY_ROOT`, the markdown root for durable memory files
- project markdown `Agent/` folder under `${AGENT_MEMORY_ROOT}/projects/<Project>/.../Agent`

Ask for the markdown memory path if it cannot be inferred.

## Deterministic Repo Effects

- `.context/progress.md` exists with a short progress template.
- `.gitignore` contains `.context/progress.md`.
- `AGENTS.md` has `## Context and precedence`.
- `AGENTS.md` points agents to the project `Agent/Memory/index.md`.
- `AGENTS.md` explains that `$agent-memory` distills progress into real memory notes only when durable context exists.

Use `references/agents.md` as the canonical source for deterministic `AGENTS.md` snippets. The setup script should render those snippets instead of retyping them.

Do not add project-specific doctrine beyond the memory plumbing.
