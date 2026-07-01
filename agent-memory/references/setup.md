# Setup Reference

Setup mode installs deterministic project plumbing. Keep edits minimal and idempotent.

## Required Inputs

- repo root
- project Obsidian `Agent/` folder, usually `${OBSIDIAN_VAULT_PATH}/projects/<Project>/.../Agent`

Ask for the Obsidian path if it cannot be inferred.

## Deterministic Repo Effects

- `.context/progress.md` exists with a short progress template.
- `.gitignore` contains `.context/progress.md`.
- `AGENTS.md` has `## Context and precedence`.
- `AGENTS.md` points agents to the project `Agent/Memory/index.md`.
- `AGENTS.md` explains that `$agent-memory` distills progress into real memories only when durable context exists.

Use `references/agents.md` as the canonical source for deterministic `AGENTS.md` snippets. The setup script should render those snippets instead of retyping them.

Do not add project-specific doctrine beyond the memory plumbing.
