---
name: gh-pr-creation
description: Create a new GitHub pull request end-to-end when the user asks to open or create a PR. Use when Codex must turn local uncommitted work into a reviewable PR by making multiple scoped commits, running and passing all repository quality gates, renaming the branch so it reflects the changes, creating a Conventional Commits PR title, writing a PR description with summary/rationale/migration steps, and assigning Copilot as reviewer.
---

# GitHub PR Creation

Follow this workflow every time the user asks to create a new PR.

## 1) Prepare and scope commits

- Inspect pending changes with `git status --short` and `git diff --name-only`.
- Split work into multiple logical, reviewable commit groups.
- Keep each commit focused on one concern (for example: refactor, API change, tests, docs).
- Create granular commits with clear messages.
- Do not leave unrelated changes in a commit.

## 2) Run and pass all quality gates before PR creation

- Identify required project quality gates from repo config and CI conventions.
- Run all required checks locally and ensure they pass before opening the PR.
- If any check fails, fix the issue and rerun until all checks pass.
- Confirm the working tree is clean after commits with `git status --short`.

## 3) Rename the branch to match the change

- Derive a branch name that clearly reflects the implemented change.
- Rename the current branch before PR creation:
  - `git branch -m <new-branch-name>`
- If needed, push the renamed branch and set upstream:
  - `git push -u origin <new-branch-name>`

## 4) Create the PR with required metadata

- PR title must follow Conventional Commits format:
  - `<type>(<scope>): <short description>`
- Write a PR description that includes:
  - Summary of changes.
  - Rationale (why the change is needed).
  - Migration steps (or explicit `None` if no migration is needed).
  - Never use `\n` for newlines in the description, always use actual newlines.
- Create the PR using `gh pr create` with explicit title and body.

## 5) Assign Copilot reviewer (required)

- After PR creation, resolve the PR number.
- MUST add Copilot reviewer with:
  - `gh pr edit <PR number> --add-reviewer "copilot-pull-request-reviewer"`

Do not skip reviewer assignment.

## 6) Report completion details

- Provide PR URL.
- List commits included.
- Confirm quality gates passed before PR creation.
