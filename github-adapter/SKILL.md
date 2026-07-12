---
name: github-adapter
description: Execute authenticated GitHub CLI operations and resolve canonical repository, issue, and pull request references for other skills.
---

# github-adapter

Use `scripts/github_adapter.py` from workflow scripts instead of invoking `gh`
directly. Resolve repository, issue, and pull request references before applying
consumer-specific policy.

## Rules

- Call `GitHub.authenticate()` at direct workflow entry points.
- Use `text`, `bytes`, or `json` for normalized command results.
- Use `resolve_repository`, `resolve_issue`, or `resolve_pr` for explicit or
  current context. URL references own their repository scope.
- Inject a runner only in focused adapter tests; consumers retain their policy,
  queries, pagination, and result classification.
- Fail when this skill is unavailable. Do not copy or fall back to GitHub
  transport or reference parsing in a consumer.
