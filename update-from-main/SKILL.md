---
name: update-from-main
description: Safely sync attached non-`main` worktree branch with fetched `origin/main`. Use when asked to update, merge, or bring main into current branch.
---

# update-from-main

Run `python3 <skill>/scripts/update_from_main.py`.

Helper fetches before mutation, stashes tracked/untracked state plus colliding ignored paths, and merges exact `main_sha`.

- `status=merged` or `status=up_to_date`: report emitted refs, SHAs, and stash state.
- `status=merge_conflict`: resolve intended behavior, `git add <paths>`, `GIT_EDITOR=true git merge --continue`; then apply non-`none` `stash` OID with `git stash apply --index <oid>`.
- `status=merge_pending`: fix failed merge hook, `GIT_EDITOR=true git merge --continue`, then apply non-`none` `stash` OID.
- `status=submodule_update_required`: inspect and update initialized submodules with `git submodule update --checkout --recursive`, then apply non-`none` `stash` OID.
- `status=stash_conflict`: resolve and stage every stash conflict; retain and report stash OID.
- `status=stash_restore_failed`: retain and report stash OID, inspect files and `git stash show --include-untracked <oid>`, then restore clear changes. Ask user which version wins for upstream-path collision; never drop backup first.
- After recovery, run `git status --short` and smallest relevant check. Never rebase, reset, abort, push, or commit unrelated work.
