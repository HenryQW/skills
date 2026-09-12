---
name: gh
description: Look up exact GitHub CLI commands, arguments, flags, examples, and behavior from a versioned local manual. Use when asked how to use `gh` or when exact `gh` syntax or options must be checked.
---

# gh

Use the bundled manual instead of recalling GitHub CLI syntax.

## Load progressively

Mirror command words under `references/commands/`; for example, `gh pr create` maps to `pr/create/`.

1. Read only the deepest known command `README.md`. It contains purpose, usage, aliases, child routes, and facet links.
2. Read only the needed linked facet: `options.md` for flags, `details.md` for arguments or constraints, or `examples.md` for examples.
3. Read sibling `help.txt` only when facets do not settle the answer or exact raw wording is required.

If the command path is uncertain, start at the nearest known parent README and follow one child. Never load sibling directories or the whole manual. Shared topics live in `references/topics/`; read only the needed topic such as `environment.md`, `exit-codes.md`, or `formatting.md`.

## Use the manual

- Answer with the shortest valid command and only relevant caveats. Do not execute it unless requested.
- Never invent flags, output fields, defaults, or behavior.
- Check `references/snapshot.txt` when version matters. If installed `gh` differs, the command is absent, or current behavior is required, run `gh help <command path>` and trust live help.

Local aliases and extensions may not exist elsewhere. Regenerate references with `python3 <skill>/scripts/generate.py`.
