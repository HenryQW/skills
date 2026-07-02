---
name: issue-to-code
description: Use this skill when asked to implement a GitHub issue into a clean feature branch. It reads the issue, creates an issue branch, applies a minimal implementation, commits the result, and returns only the branch name. Do not use this skill for review loops, PR creation, or fixing Greptile feedback.
---
# issue-to-code

## Goal

Implement one GitHub issue into a clean feature branch with the smallest intentional diff.
Stop after committing. Do not push, open a PR, or run Greptile.

## Bundled resources

- `scripts/issue_snapshot.py`: compact issue text and comments.
- `scripts/branch_name.py`: deterministic branch names.
- `scripts/diff_guard.py`: forbidden-path guard.

## Inputs

- `issue_number` is required.
- `base_branch` is optional and defaults to the repository default branch.
- `branch_slug` is optional.

## Scope and boundaries

- Only modify files required by the issue.
- Do not perform unrelated refactors.
- Do not modify secrets, env files, generated files, lockfiles, `.context/`, `.agents/`, or infrastructure files unless the issue explicitly requires it.
- Do not use `git add .` unless the full diff has been inspected.
- Use Conventional Commits.
- Return only the branch name on success.

Stop instead of guessing when the issue is not actionable, requires a product decision, or would require forbidden-path changes not explicitly required by the issue.

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

### 9. Final verification

Run:

```bash
git status --short
git log --oneline -5
git branch --show-current
```

The working tree must be clean.

## Output

Return only the current branch name.

Do not include explanations.

Do not include summaries.

Do not include test notes.

Do not include markdown.
