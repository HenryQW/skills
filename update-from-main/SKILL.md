---
name: update-from-main
description: Update current worktree branch from remote main with exact refs, stashing local changes and resolving conflicts. Use when asked to sync, update, or bring main into current worktree or branch.
---

# update-from-main

Update current worktree branch from `origin/main`.

1. Run:

   ```bash
   python3 <skill>/scripts/update_from_main.py
   ```

2. Helper accepts only attached non-`main` branch. It fetches `+refs/heads/main:refs/remotes/origin/main` before mutation, pins `main_sha`, then stashes tracked/untracked state plus ignored paths that collide with source.
3. `status=merged` or `status=up_to_date` ends work. Report emitted refs, SHAs, and stash state.
4. On `status=merge_conflict`, agent must solve every conflict in current worktree: inspect both sides, preserve intended behavior, `git add <paths>`, then `GIT_EDITOR=true git merge --continue`. If `stash_oid` is not `none`, run `git stash apply --index <stash_oid>` after merge completion.
5. On `status=stash_conflict`, agent must solve every stash conflict and retain backup `stash_oid`.
6. On `status=stash_restore_failed`, retain `stash_oid`; inspect current files and `git stash show --include-untracked <stash_oid>`. Restore clear changes. Ask user which version wins for an upstream-path collision; never drop backup first.
7. After conflict recovery, inspect `git status --short` and run smallest relevant project check. Never rebase, reset, abort, commit unrelated work, or push.
