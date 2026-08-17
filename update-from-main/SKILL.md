---
name: update-from-main
description: Safely sync attached non-`main` worktree branch with fetched `origin/main`. Use when asked to update, merge, or bring main into current branch.
---

# update-from-main

Run `python3 <skill>/scripts/update_from_main.py` once. Helper fetches before mutation, stashes tracked/untracked state plus colliding ignored paths, and merges exact emitted `main` SHA.

## Fast path

For `status=merged` or `status=up_to_date`, report emitted line, run:

```bash
git status --short --branch
git diff --check <emitted-before-sha> HEAD
```

Stop. No tests, install, history scan, push, extra commit, or helper rerun.

## Recovery

Emitted `main` SHA is authoritative for run. Do not rerun because `origin/main` advances. Never rerun while emitted stash remains retained; finish current recovery first.

- `status=merge_conflict`: resolve and `git add <paths>`; run `GIT_EDITOR=true git merge --continue`, then apply non-`none` stash with `git stash apply --index <oid>`.
- `status=merge_pending`: fix failed merge hook, run `GIT_EDITOR=true git merge --continue`, then apply non-`none` stash.
- `status=submodule_update_required`: run `git submodule update --checkout --recursive`, then apply non-`none` stash.
- `status=stash_conflict`: resolve and stage every emitted conflict path; retain and report stash OID.
- `status=stash_restore_failed`: retain and report stash OID. Inspect once with `git stash show --name-status --include-untracked <oid>`, restore clear changes, and ask user only when one upstream-path collision version must win. Never drop backup first.

Start conflict triage with emitted JSON conflict path list, then inspect marker line numbers one separately quoted path at a time:

```bash
git show --no-patch --oneline <emitted-main-sha>
grep -nE '^(<<<<<<<|=======|>>>>>>>)' -- '<one-conflict-path>'
```

Inspect bounded source regions around markers. Never dump full `git diff --cc` across files. Use bounded `git show :2:path | sed -n '<start>,<end>p'` and `git show :3:path | sed -n '<start>,<end>p'` only when hunk lacks context. Prefer upstream for unrelated changes; combine compatible overlapping behavior. Ask user only when intent cannot determine one required semantic winner.

Resolve source first. Regenerate lockfiles and build artifacts instead of reading generated conflicts. For docs/index conflicts, keep entries whose paths exist, add upstream paths, remove deleted paths, and avoid full-repo scans.

After recovery, verify exact source merged:

```bash
git merge-base --is-ancestor <emitted-main-sha> HEAD
git status --short --branch
```

Run only smallest relevant check; docs-only recovery gets docs-specific checks, not broad tests. Run project dependency preflight before dependency-backed checks. Redirect check output to temp file. On success report command plus `PASS`; on failure print only final 100 lines. Never rebase, reset, abort, push, or commit unrelated work.
