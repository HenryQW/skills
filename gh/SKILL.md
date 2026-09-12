---
name: gh
description: Look up exact GitHub CLI commands, arguments, flags, examples, and behavior from a versioned local manual. Use when asked how to use `gh` or when exact `gh` syntax or options must be checked.
---

# gh

Use the bundled manual instead of recalling GitHub CLI syntax.

## Load progressively

Mirror command words as nested directories. Read only the deepest known `README.md`:

- `gh` → `references/commands/README.md`
- `gh pr` → `references/commands/pr/README.md`
- `gh pr create` → `references/commands/pr/create/README.md`

If the path is uncertain, start at the nearest known parent; its help lists immediate children. Never load sibling command directories or the whole manual.

Shared topics live in `references/topics/`; read only the needed topic such as `environment.md`, `exit-codes.md`, or `formatting.md`.

## Use the manual

1. Extract exact positional arguments, flags, defaults, constraints, and examples from the selected command page.
2. Answer with the shortest valid command and only relevant caveats. Do not execute it unless requested.
3. Never invent flags, output fields, defaults, or command behavior.
4. Check `references/snapshot.txt` when version matters. If installed `gh` differs, the command is absent, or current behavior is required, run `gh help <command path>` and trust live help over the snapshot.

Local aliases and extensions captured in the snapshot may not exist elsewhere. Regenerate all references from installed `gh` with `python3 <skill>/scripts/generate.py`.
