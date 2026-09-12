---
name: gh
description: Look up exact GitHub CLI commands, arguments, flags, examples, and behavior from a versioned local manual. Use when asked how to use `gh` or when exact `gh` syntax or options must be checked.
---

# gh

Use the bundled manual instead of recalling GitHub CLI syntax.

## Load progressively

Mirror command words under `references/commands/`; for example, `gh pr create` maps to `pr/create/`.

1. Read only the deepest known command `README.md`. It contains purpose, usage, aliases, child routes, and every command-specific option.
2. Read only the needed linked facet: `details.md` for arguments or constraints, or `examples.md` for examples.
3. Read sibling `help.txt` only when compact files do not settle the answer or source wording is required.

If the command path is uncertain, start at the nearest known parent README and follow one child. Never load sibling directories or the whole manual. Shared topics live in `references/topics/`; read only the needed compact topic. Use command routes instead of the omitted redundant `actions` topic; telemetry controls are in `environment.md`.

## Use the manual

- Every command accepts `--help`; it is intentionally omitted from command references.
- Answer with the shortest valid command and only relevant caveats. Do not execute it unless requested.
- Never invent flags, output fields, defaults, or behavior.
- Check `references/snapshot.txt` when version matters. If installed `gh` differs, the command is absent, or current behavior is required, run `gh help <command path>` and trust live help.

Local aliases and extensions may not exist elsewhere.

## Update the snapshot

1. Install/select the intended `gh` version and run `python3 <skill>/scripts/generate.py`. Never hand-edit generated command or topic references.
2. Inspect `references/snapshot.txt`, command/topic source diffs, and added or removed paths. If a topic's structure changed, update its deterministic renderer in `scripts/topics.py`; its shape checks fail rather than silently dropping new content.
3. Update the root README's displayed version to exactly match the snapshot.
4. Run `python3 <skill>/scripts/test_compact.py`, `python3 <skill>/scripts/test_topics.py`, then `python3 <repo>/scripts/validate.py`.
