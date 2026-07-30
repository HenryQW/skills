---
name: git-commit
description: Create a Conventional Commit from current repository changes. Use when asked to commit changes, create a git commit, or run /commit.
---

# git-commit

Commit one logical change from the actual diff.

1. Inspect `git status --short`, `git diff`, and `git diff --staged`.
2. Treat staged files as intended scope. If nothing is staged, stage only one clear logical change. Stop when scope is ambiguous or includes unrelated files. Never stage secrets.
3. Derive `<type>[(scope)][!]: <imperative description>` from the staged diff. Use `feat`, `fix`, `docs`, `style`, `refactor`, `perf`, `test`, `build`, `ci`, `chore`, or `revert`; keep the description under 72 characters. Add a body only for needed context and `BREAKING CHANGE:` or issue footers when applicable.
4. Run `git commit` without changing git config, bypassing hooks, amending, or using destructive commands. If a hook fails, fix only the scoped failure and create a new commit; never amend unless explicitly requested.
5. Report the commit hash and message.
