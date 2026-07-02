---
name: issue-to-code
description: Use this skill when asked to implement a GitHub issue into a clean feature branch. It reads the issue, creates an issue branch, applies a minimal implementation, commits the result, and returns only the branch name. Do not use this skill for review loops, PR creation, or fixing Greptile feedback.
---
# issue-to-code

## Goal

Implement a GitHub issue into a clean feature branch with a minimal intentional diff.
This skill stops after committing the implementation.
It does not run Greptile review.
It does not push.
It does not create a PR.

## Bundled resources

- Use `scripts/branch_name.py` to generate the issue branch name when preparing the branch.
- Read `references/implementation-checklist.md` when deciding scope, validation, or staging.

## Inputs

- `issue_number` is required.
- `base_branch` is optional and defaults to the repository default branch.
- `branch_slug` is optional.

## Hard boundaries

- Only modify files required by the issue.
- Do not perform unrelated refactors.
- Do not modify secrets, env files, generated files, lockfiles, `.context/`, `.agents/`, or infrastructure files unless the issue explicitly requires it.
- Do not use `git add .` unless the full diff has been inspected.
- Use Conventional Commits.
- Return only the branch name on success.

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
gh issue view <issue_number> --comments
```

Extract:

- Requirements.
- Acceptance criteria.
- Explicit constraints.
- Files, modules, or behaviors mentioned in the issue.

Stop if the issue does not contain an actionable implementation request.

Do not invent product behavior.

When the issue is partially ambiguous, make the smallest reasonable implementation that satisfies the explicit issue text.

### 3. Prepare the branch

Run:

```bash
git fetch origin
git checkout <base_branch>
git pull origin <base_branch>
```

Create the branch name with the helper:

```bash
python3 <skill_dir>/scripts/branch_name.py <issue_number> [branch_slug]
```

Then create the branch:

```bash
git checkout -b <branch_name>
```

### 4. Inspect the repository before editing

When scope is unclear, read `references/implementation-checklist.md`.

Identify the smallest relevant files or modules.

Prefer existing patterns over new abstractions.

Do not introduce new dependencies unless the issue explicitly requires them.

Do not expand scope to adjacent cleanup.

### 5. Implement the issue

Apply the smallest code change that satisfies the issue.

Keep changes local, traceable, and reviewable.

Add or update tests only when they directly validate the issue behavior.

Do not make broad formatting changes.

Do not touch unrelated files.

### 6. Inspect the diff

Run:

```bash
git status --short
git diff --stat
git diff
```

Check:

- Every changed file is related to the issue.
- The diff is minimal.
- No unrelated formatting or refactoring slipped in.
- No secrets, env files, generated files, lockfiles, .context/, .agents/, or infrastructure files were changed unless explicitly required.

Stop if the diff contains unrelated changes.

### 7. Run relevant local validation

Use `references/implementation-checklist.md` for validation discovery.

Run the smallest relevant tests, type checks, linters, or build commands that are discoverable from the repository.

Prefer targeted commands over full-suite commands when the issue is narrow.

If no validation command is obvious, continue but note that tests were not run in the internal commit planning.

Do not add extra files just to satisfy local tooling unless the issue requires it.

### 8. Commit

Stage only inspected files.

Use explicit file paths.

Example:

```bash
git add <file1> <file2>
```

Do not use git add . unless the entire diff has been inspected and every changed file is intentional.

Create one or more Conventional Commits.

Each commit must represent one logical unit.

Do not mix categories in one commit.

Allowed commit types:

- feat
- fix
- test
- refactor
- chore
- docs

Example:

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

The working tree should be clean.

## Output

Return only the current branch name.

Do not include explanations.

Do not include summaries.

Do not include test notes.

Do not include markdown.
