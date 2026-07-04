---
name: issue-workbench
description: Use this skill when asked to implement one GitHub issue into a clean feature branch. It reads the issue, creates an issue branch in the current worktree by default, applies a minimal implementation, runs review-checkpoint or adversarial review fallback, commits the result, and either hands off to pr-launchpad or returns a branch to shipyard integration mode.
---

# issue-workbench

## Goal

Implement one GitHub issue into a clean feature branch with the smallest intentional diff.
Run `$review-checkpoint` or its fallback review gate on that branch and fix actionable findings before returning.
After the latest completed review gate returns no actionable findings, hand off to pr-launchpad on the current branch unless `handoff_mode=integration_branch`.

## Bundled resources

- `scripts/issue_snapshot.py`: compact issue text and comments.
- `scripts/branch_name.py`: deterministic branch names.
- `scripts/start_issue_branch.py`: branch and shipyard worktree setup.
- `scripts/integration_child.py`: integration-mode start, finish, and merge glue.
- `scripts/diff_guard.py`: forbidden-path guard.

Use `<issue_workbench_dir>` as the absolute path to this skill directory when running `diff_guard.py`.

## Inputs

- `issue_number` is required.
- `base_branch` is optional and defaults to the repository default branch.
- `branch_slug` is optional.
- `max_iterations` is optional and passes through to `$review-checkpoint`.
- `poll_interval_seconds` is optional and passes through to `$review-checkpoint`.
- `worktree_path` is optional. When set, create the issue branch in that new Git worktree instead of the caller worktree.
- `handoff_mode` is optional and defaults to `pull_request`. The only other supported value is `integration_branch`.
- `integration_branch` is required when `handoff_mode=integration_branch` and is the local branch that the issue branch will be merged back into by `$shipyard`.

## Scope and boundaries

- Only modify files required by the issue.
- `$review-checkpoint` is the preferred review signal and owns review-actionability rules.
- If `$review-checkpoint` itself cannot run, use the adversarial review fallback in step 9.
- Do not perform unrelated refactors.
- Do not modify secrets, env files, generated files, lockfiles, `.agents/`, or infrastructure files unless the issue explicitly requires it or the review gate directly identifies a deterministic issue in that file.
- Do not modify `.context/` except local uncommitted review-checkpoint notes in `.context/progress.md`.
- Do not use `git add .` unless the full diff has been inspected.
- Use Conventional Commits.
- Return only the PR URL on success unless `handoff_mode=integration_branch`.

Stop instead of guessing when the issue is not actionable, requires a product decision, or would require forbidden-path changes not explicitly required by the issue.

Ignore review findings that `$review-checkpoint` classifies as non-actionable. Stop when a real risk requires a product decision or when a finding repeats after a reasonable targeted fix.

## Procedure

### 1. Confirm clean working tree

Run:

```bash
git status --short
```

If there are existing uncommitted changes, stop unless the user explicitly asked to continue with the existing worktree.

Do not overwrite or discard user changes.

### 2. Read the issue

Run:

```bash
python3 <skill_dir>/scripts/issue_snapshot.py <issue_number>
```

If truncation or omitted comments hide context needed to decide scope, rerun it with larger limits before implementing.

Extract explicit requirements, acceptance criteria, constraints, named files, named modules, and named behavior. Use that as the implementation scope. Do not invent product behavior.

### 3. Prepare the branch

Use the current worktree by default. Use `worktree_path` only when `$shipyard` passes it for integration work.

If `handoff_mode=integration_branch`, require `worktree_path` and `integration_branch`.

Use the helper for normal PR mode:

```bash
python3 <skill_dir>/scripts/start_issue_branch.py <issue_number> [--base-branch <base_branch>] [--branch-slug <branch_slug>]
```

For `$shipyard` integration mode:

```bash
python3 <skill_dir>/scripts/integration_child.py start <issue_number> --worktree-path <worktree_path> --integration-branch <integration_branch> [--branch-slug <branch_slug>]
```

After integration setup succeeds, `cd` into the returned worktree. Do not switch branches in the caller worktree when `worktree_path` is set.

Use `<review_base>=<integration_branch>` in integration mode. Otherwise use `<review_base>=origin/<base_branch>`.

### 4. Inspect the repository before editing

Identify the smallest relevant files or modules with `rg` or `rg --files`. Prefer existing patterns, tests, helpers, and conventions. Avoid new dependencies unless the issue requires them.

### 5. Implement

Apply the smallest code change that satisfies the issue. Add or update tests only when they directly validate requested behavior.

### 6. Inspect the diff

Run:

```bash
git status --short
git diff --stat
git diff
python3 <issue_workbench_dir>/scripts/diff_guard.py --base <review_base>
```

If the issue explicitly requires a blocked path, verify that requirement in the issue text, then rerun the guard with `--base <review_base> --allow <path>`.

Every changed file and line must trace to the issue. Stop if the diff contains unrelated changes.

### 7. Run relevant local validation

Run the smallest relevant validation command discoverable from nearby tests, `package.json`, `pyproject.toml`, `tox.ini`, `noxfile.py`, `pytest.ini`, or `Makefile`. If no command is obvious, continue without inventing tooling.

### 8. Commit

Stage explicit inspected paths only:

```bash
git add <file1> <file2>
```

Commit one logical unit at a time with Conventional Commits:

```bash
git commit -m "feat(auth): add token refresh handling"
```

### 9. Review gate

Run `$review-checkpoint` with the selected `max_iterations` and `poll_interval_seconds`.

After any review-gate fix changes or commits files, rerun the path guard before handoff:

```bash
python3 <issue_workbench_dir>/scripts/diff_guard.py --base <review_base>
```

If that fails because `.context/progress.md` is local scratch, first confirm `git diff --name-only <review_base>...HEAD -- .context/progress.md` is empty before adding `--allow .context/progress.md`.

If the review gate directly identifies a deterministic issue in a blocked path, verify that finding before adding `--allow <path>`.

Rerun `python3 <issue_workbench_dir>/scripts/diff_guard.py --base <review_base>` with only the verified `--allow` values accumulated above.

If `$review-checkpoint` tooling is unavailable, spawn one read-only adversarial reviewer instead. Give it the issue scope, review base, changed files, `git diff --stat <review_base>...HEAD`, `git diff <review_base>...HEAD`, and verification commands/results. Tell it not to edit files, commit, push, or review broad cleanup. Classify its findings with `$review-checkpoint` actionability rules.

If the fallback reviewer finds an actionable issue, fix and commit it, then run `$review-checkpoint` again; if it is still unavailable, run another fallback reviewer.

Continue only after the latest completed review gate reports no actionable findings with no later commit.

### 10. Final handoff

Run:

```bash
git status --short
git log --oneline -5
git branch --show-current
git rev-parse HEAD
git diff --stat <review_base>...HEAD
```

No staged or tracked code changes should remain before pr-launchpad runs or before integration-mode return. `.context/progress.md` may remain local and uncommitted for review-checkpoint notes.

If `handoff_mode=pull_request`, run `pr-launchpad` on the current branch and return only the PR URL.

If `handoff_mode=integration_branch`, do not run `pr-launchpad`. Return exactly:

```text
branch=<branch_name>
worktree=<worktree_path>
commit=<commit_sha>
diff_stat=<git diff --stat <review_base>...HEAD output with newlines replaced by " | ">
verification=<pass|skip>:<commands run or skip reason>
```

Prefer generating those lines with:

```bash
python3 <skill_dir>/scripts/integration_child.py finish --review-base <review_base> --verification <pass|skip>:<commands run or skip reason>
```

## Output

In normal PR mode, return only the PR URL.

In integration mode, return only the branch, worktree, commit, diff_stat, and verification lines described above.

Do not include explanations.

Do not include extra summaries or test notes beyond the exact required return lines.

Do not include markdown.
