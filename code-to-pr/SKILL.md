---
name: code-to-pr
description: Use this skill when asked to push the current review-clean issue branch and open a GitHub pull request. It returns only the PR URL. Do not use this skill to implement a fresh issue or run Greptile review.
---
# code-to-pr

## Goal

Push the current non-base branch and open a PR.
Assume implementation and Greptile review fixes already exist.

## Bundled resources

- `scripts/diff_guard.py`: forbidden-path guard.
- `scripts/pr_body.py`: fallback PR body generation.

## Inputs

- `base_branch` is required.
- `issue_number` is optional.

## Scope and boundaries

- Do not run on the base branch.
- Treat `git diff <base_branch>...HEAD` as the implementation scope.
- Do not run Greptile.
- Do not modify code.
- Do not use issue text to expand scope; use it only for `Closes` vs `Refs`.
- Do not expand product scope.
- Do not perform unrelated refactors.
- Do not use `git add .` unless the full diff has been inspected.
- Do not commit.
- Return only the PR URL on success.

Stop if the branch is not ready to publish, the diff contains unrelated or forbidden files, or PR content requires a product decision.

## Procedure

### 1. Confirm branch and working tree

Run:

```bash
git branch --show-current
git status --short
```

Stop if the current branch is base_branch.

If the working tree is dirty, inspect the diff before continuing.

Continue only when the dirty state is local `.context/progress.md` review IDs. Otherwise stop. Do not overwrite, stage, commit, or discard user changes.

### 2. Establish diff scope

Run:

```bash
git diff <base_branch>...HEAD --stat
git diff <base_branch>...HEAD
python3 <skill_dir>/scripts/diff_guard.py --base <base_branch> --allow .context/progress.md
```

Use this diff as the PR scope.

### 3. Push

Run:

```bash
git push --set-upstream origin HEAD
```

### 4. Create PR

Inspect whether the repository has a PR template.

Use the PR template if present.

If no PR template exists, draft a body with:

```bash
python3 <skill_dir>/scripts/pr_body.py <base_branch> [--issue-number <issue_number>] [--issue-link closes|refs] [--test <command-or-result>] [--body-file <path>]
```

Default to `Refs` when issue_number is provided.

Use `Closes` only when the issue has been inspected and the branch fully resolves it:

```text
Closes #<issue_number>
```

Otherwise include:

```text
Refs #<issue_number>
```

Use a concise title.

Prefer:

```text
Fix #<issue_number>
```

or a short behavior-focused title when more descriptive.

Create the PR non-interactively:

```bash
current_branch=$(git branch --show-current)
gh pr create --base <base_branch> --head "$current_branch" --title "<title>" --body-file <body_file>
```

### 5. Output

Return only the PR URL.

Do not include explanations.

Do not include summaries.

Do not include markdown.
