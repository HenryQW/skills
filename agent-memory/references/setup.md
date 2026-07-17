# Setup Reference

Load this reference only when the invocation includes `--setup`. Normal context loading, capture, and distillation never run setup.

## Prerequisites

Export the absolute path to the Obsidian vault in the environment that launches the agent:

```bash
export OBSIDIAN_ROOT="/absolute/path/to/Obsidian/vault"
```

Persist that command in the appropriate shell or launcher configuration, then restart the agent. Setup verifies the variable and directory but never edits shell files.

Provide two explicit inputs:

- repository root
- path relative to the vault, such as `Project_Name`

The project declaration becomes:

```text
OBSIDIAN_PROJECT=${OBSIDIAN_ROOT}/Project_Name
```

## Preview and Apply

From the installed skill folder, preview all changes:

```bash
python3 scripts/setup_agent_memory.py \
  --project-root /path/to/project \
  --obsidian-project Project_Name
```

Review the displayed diffs. After explicit approval, apply the same plan using its confirmation hash:

```bash
python3 scripts/setup_agent_memory.py \
  --project-root /path/to/project \
  --obsidian-project Project_Name \
  --apply --confirm <preview-hash>
```

Any intervening change invalidates the hash and requires a new preview.

## Effects

Setup changes only these surfaces:

- adds one marked block to `~/.codex/AGENTS.md` without replacing existing instructions
- installs the bundled workflow at `${OBSIDIAN_ROOT}/agent/knowledge-workflow.md`
- adds the exact `OBSIDIAN_PROJECT` declaration to the project `AGENTS.md`
- creates `.context/progress.md` and the agent-memory entries in `.gitignore`
- creates `${OBSIDIAN_PROJECT}/Agent/Memory/index.md`, `Decisions/`, and `Guidance/`

Existing identical content is left unchanged. Conflicting declarations, marked blocks, workflow files, paths, or symlinks stop setup without overwriting them.
