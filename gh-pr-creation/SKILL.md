---
name: gh-pr-creation
description: Create or publish a GitHub pull request when asked to open or create a PR. Use when Codex must turn local changes or the current clean branch into a reviewable PR by scoping the diff, committing any pending work, running relevant quality gates, pushing the branch, creating a Conventional Commits PR title, and writing the fixed PR body template with optional issue closure.
---

# GitHub PR Creation

Follow this workflow every time the user asks to create a new PR.

## Inputs

- `base_branch` is required unless obvious from repository context.
- `issue_number` is optional.

## Boundaries

- Do not implement fresh product work.
- Do not run Greptile.
- Do not modify secrets, env files, generated files, lockfiles, `.context/`, `.agents/`, or infrastructure files unless the user explicitly asks.
- Do not use `git add .` unless the full diff has been inspected.
- Stop instead of guessing when the PR scope or issue closure status requires a product decision.

## 1) Scope the diff

- Run `git branch --show-current` and `git status --short`.
- Stop if the current branch is `base_branch`.
- Run `git diff <base_branch>...HEAD --stat` and `git diff <base_branch>...HEAD`.
- Treat `git diff <base_branch>...HEAD` as the PR scope.
- If the working tree is dirty, inspect `git diff`, `git diff --cached`, and untracked files before continuing.
- Continue only when every changed file belongs in the PR.

## 2) Commit pending work

- Inspect pending changes with `git status --short` and `git diff --name-only`.
- Split work into multiple logical, reviewable commit groups.
- Keep each commit focused on one concern (for example: refactor, API change, tests, docs).
- Create granular Conventional Commits.
- Do not leave unrelated changes in a commit.

## 3) Run quality gates

- Identify required project quality gates from repo config and CI conventions.
- Run all required checks locally and ensure they pass before opening the PR.
- If any check fails, fix the issue and rerun until all checks pass.
- Confirm the working tree is clean after commits with `git status --short`.

## 4) Rename the branch when needed

- Skip branch renaming when the current branch is already specific and publishable.
- Otherwise derive a branch name that clearly reflects the implemented change:
  - `git branch -m <new-branch-name>`
- If needed, push the renamed branch and set upstream:
  - `git push -u origin <new-branch-name>`

## 5) Push

- Push the current branch:
  - `git push --set-upstream origin HEAD`

## 6) Create the PR

- Derive the PR title from the branch's Conventional Commit subjects:
  - Run `git log --format=%s <base_branch>..HEAD`.
  - Stop if no branch commit subject follows Conventional Commits.
  - If there is one commit, use that subject.
  - If there are multiple commits, use the best single Conventional Commit title that summarizes the PR.
  - Do not use issue-only titles such as `Fix #123` unless they are also valid Conventional Commits.
- Write the PR body with this fixed template:

```markdown
## Summary
- <2 to 4 bullets describing the intentional changes>

## Testing
- <commands run, with result>
- <or "Not run">

## Scope
- <notable exclusions or constraints>

Closes #<issue_number>
```

- Omit the `Closes #<issue_number>` line when `issue_number` is not provided.
- Use `Closes #<issue_number>` only when the PR fully resolves that issue. If not, use `Refs #<issue_number>`.
- Never use `\n` for newlines in the description; use actual newlines.
- Create the PR non-interactively:
  - `gh pr create --base <base_branch> --head "$(git branch --show-current)" --title "<conventional-commit-title>" --body-file <body_file>`

## 7) Report completion details

- Provide PR URL.
- List commits included.
- Confirm quality gates passed before PR creation.
