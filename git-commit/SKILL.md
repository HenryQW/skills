---
name: git-commit
description: Create scoped Conventional Commits from current repository changes against a target branch. Use when asked to commit changes, create git commits, or run /commit.
---

# git-commit

Commit current changes as coherent scoped commits.

1. Resolve `<target>` from explicit user input, the current PR base, or the repository default branch, in that order. Stop if ambiguous; never infer it from the branch name.
2. Inspect `git status --short`, `git diff --staged`, and `git diff "$(git merge-base HEAD <target>)"` to understand the full target-branch delta. Include untracked files from status; never stage secrets or `.context/`.
3. Partition uncommitted changes by purpose and codebase scope. Keep implementation, tests, and required docs for one change together; separate unrelated changes. Preserve coherent existing staging, stop before overriding ambiguous staging, and never rewrite existing commits. If only one coherent group exists, create one commit.
4. For each group, stage only its files or hunks and inspect `git diff --staged`. Stop if the group cannot be separated safely or its intent is unclear.
5. Derive `<type>[(scope)][!]: <imperative description>` from each staged group. Use `feat`, `fix`, `docs`, `style`, `refactor`, `perf`, `test`, `build`, `ci`, `chore`, or `revert`; keep the description under 72 characters. Add a body only for needed context and `BREAKING CHANGE:` or issue footers when applicable.
6. Run `git commit` for each group without changing git config, bypassing hooks, amending, or using destructive commands. If a hook fails, fix only that group's scoped failure and create a new commit; never amend unless explicitly requested.
7. Report the commit hashes and messages in order, plus any remaining changes.
