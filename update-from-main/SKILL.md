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

2. Helper accepts only attached non-`main` branch. It stashes tracked and untracked state, fetches `+refs/heads/main:refs/remotes/origin/main`, pins `main_sha`, then merges that exact commit.
3. `status=merged` or `status=up_to_date` ends work. Report emitted refs, SHAs, and stash state.
4. On `status=merge_conflict`, agent must solve every conflict in current worktree: inspect both sides, preserve intended behavior, `git add <paths>`, then `git merge --continue`. If `stash_oid` is not `none`, run `git stash apply --index <stash_oid>` after merge completion. On `status=stash_conflict`, solve that conflict too. Do not ask user unless intended behavior is ambiguous. Retain conflict-path stash backup and report its exact OID.
5. After conflict resolution, inspect `git status --short` and run smallest relevant project check. Never rebase, reset, abort, commit unrelated work, or push.
