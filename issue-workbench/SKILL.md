---
name: issue-workbench
description: Use this skill when asked to implement one GitHub issue into a clean feature branch. It reads the issue, creates an issue branch in the current worktree by default, applies a minimal implementation, runs review-checkpoint, commits the result, and either hands off to pr-launchpad or returns a branch to shipyard integration mode.
---

# issue-workbench

## Goal

Implement one GitHub issue into a clean feature branch with the smallest intentional diff.
Run `$review-checkpoint` on that branch and fix actionable findings before returning.
After the latest completed review-checkpoint run returns no actionable findings, hand off to pr-launchpad on the current branch unless `handoff_mode=integration_branch`.

## Bundled resources

- `scripts/issue_snapshot.py`: compact issue text and comments.
- `scripts/branch_name.py`: deterministic branch names.
- `scripts/start_issue_branch.py`: branch and shipyard worktree setup.
- `scripts/diff_guard.py`: forbidden-path guard.

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
- `$review-checkpoint` is the only review signal and owns review-actionability rules.
- Do not perform unrelated refactors.
- Do not modify secrets, env files, generated files, lockfiles, `.agents/`, or infrastructure files unless the issue explicitly requires it or review-checkpoint directly identifies a deterministic issue in that file.
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
python3 <skill_dir>/scripts/start_issue_branch.py <issue_number> --worktree-path <worktree_path> --integration-branch <integration_branch> [--branch-slug <branch_slug>]
```

After integration setup succeeds, `cd` into the returned worktree. Do not switch branches in the caller worktree when `worktree_path` is set.

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
python3 <skill_dir>/scripts/diff_guard.py
```

If the issue explicitly requires a blocked path, verify that requirement in the issue text, then rerun the guard with `--allow <path>`.

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

If review-checkpoint changes files, rerun the path guard before handoff:

```bash
python3 <skill_dir>/scripts/diff_guard.py --allow .context/progress.md
```

If review-checkpoint directly identifies a deterministic issue in a blocked path, verify that finding, then rerun the guard with `--allow .context/progress.md --allow <path>`.

Continue only after review-checkpoint reports no actionable findings from the latest completed review with no later commit.

### 10. Final handoff

Run:

```bash
git status --short
git log --oneline -5
git branch --show-current
```

No staged or tracked code changes should remain before pr-launchpad runs. `.context/progress.md` may remain local and uncommitted for review-checkpoint notes.

If `handoff_mode=pull_request`, run `pr-launchpad` on the current branch and return only the PR URL.

If `handoff_mode=integration_branch`, do not run `pr-launchpad`. Return exactly:

```text
branch=<branch_name>
worktree=<worktree_path>
```

## Output

In normal PR mode, return only the PR URL.

In integration mode, return only the branch and worktree lines described above.

Do not include explanations.

Do not include summaries.

Do not include test notes.

Do not include markdown.
