---
name: issue-workbench
description: Use this skill when asked to implement a GitHub issue into a clean feature branch. It reads the issue, creates an issue branch, applies a minimal implementation, runs Greptile review loops, commits the result, and hands off to pr-launchpad after Greptile returns no actionable findings.
---

# issue-workbench

## Goal

Implement one GitHub issue into a clean feature branch with the smallest intentional diff.
Run Greptile review loops on that branch and fix actionable findings before returning.
After the latest completed Greptile review returns no actionable findings, hand off to pr-launchpad on the current branch.

## Bundled resources

- `scripts/issue_snapshot.py`: compact issue text and comments.
- `scripts/branch_name.py`: deterministic branch names.
- `scripts/diff_guard.py`: forbidden-path guard.

## Inputs

- `issue_number` is required.
- `base_branch` is optional and defaults to the repository default branch.
- `branch_slug` is optional.
- `max_iterations` is optional and defaults to `5`.
- `poll_interval_seconds` is optional and defaults to `300`.

## Scope and boundaries

- Only modify files required by the issue.
- Greptile review sessions are the only review signal.
- Fix only actionable Greptile findings in the branch diff.
- Do not perform unrelated refactors.
- Do not modify secrets, env files, generated files, lockfiles, `.agents/`, or infrastructure files unless the issue explicitly requires it or Greptile directly identifies a deterministic issue in that file.
- Do not modify `.context/` except local uncommitted Greptile review IDs in `.context/progress.md`.
- Do not use `git add .` unless the full diff has been inspected.
- Use Conventional Commits.
- Return only the PR URL on success.

Stop instead of guessing when the issue is not actionable, requires a product decision, or would require forbidden-path changes not explicitly required by the issue.

A Greptile finding is actionable only when it refers to code visible in the branch diff, the fix is deterministic, the fix does not require a product decision, the fix does not expand issue scope, and the fix can be made in the referenced file or a directly necessary adjacent file.

Ignore findings that request clarification, broad cleanup, optional improvements, or behavior beyond the issue. Stop when a real risk requires a product decision or when a finding repeats after a reasonable targeted fix.

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

Use the provided `base_branch` input. If it is omitted, resolve the repository default branch:

```bash
base_branch=${base_branch:-$(gh repo view --json defaultBranchRef --jq .defaultBranchRef.name)}
```

Run:

```bash
git fetch origin
```

```bash
branch_name=$(python3 <skill_dir>/scripts/branch_name.py <issue_number> [branch_slug])
git checkout -b "$branch_name" "origin/$base_branch"
```

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

### 9. Greptile review and fix loop

Repeat up to `max_iterations`.

Start one Greptile review session:

```bash
greptile review --agent
```

Record the review ID returned by Greptile. Stop if no review ID is returned.

Save each review ID locally in `.context/progress.md`. Keep `.context/progress.md` uncommitted; if it appears in `git status`, do not stage it.

Retrieve or resume that review session with:

```bash
greptile review show <review_id> --agent
```

Greptile reviews are slow. If the review is still running, wait `poll_interval_seconds` seconds and run `greptile review show <review_id> --agent` again. Repeat until the review completes. Do not start another review just to poll or re-read results.

Classify findings from the full `greptile review show <review_id> --agent` output.

If no actionable findings remain, exit the loop.

Apply the smallest deterministic fixes for actionable findings, then run:

```bash
git status --short
git diff --stat
git diff
python3 <skill_dir>/scripts/diff_guard.py --allow .context/progress.md
```

If Greptile directly identifies a deterministic issue in a blocked path, verify that finding, then rerun the guard with `--allow .context/progress.md --allow <path>`.

Run the smallest relevant validation command discoverable from nearby tests, `package.json`, `pyproject.toml`, `tox.ini`, `noxfile.py`, `pytest.ini`, or `Makefile`. If no command is obvious, continue without inventing tooling.

Stage explicit inspected paths only and commit review fixes with Conventional Commits. Use `fix` unless another type is clearly more accurate.

Each iteration must resolve at least one actionable finding or reduce the actionable finding set. After committing review fixes, start a new Greptile review session for the changed branch diff.

Use the latest completed Greptile review session as the final gate only when no commit happened after it. Stop if actionable findings remain after the iteration budget.

### 10. Final handoff

Run:

```bash
git status --short
git log --oneline -5
git branch --show-current
```

No staged or tracked code changes should remain before pr-launchpad runs. `.context/progress.md` may remain local and uncommitted for review IDs.

Then run `pr-launchpad` on the current branch and return only the PR URL.

## Output

Return only the PR URL.

Do not include explanations.

Do not include summaries.

Do not include test notes.

Do not include markdown.
