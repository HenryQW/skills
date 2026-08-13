---
name: pr-comment-sweep
description: Fetch GitHub pull request comments with gh, assess actionable feedback, propose fixes, then apply, validate, commit, and push accepted fixes. Use when asked to sweep, address, or fix PR comments end to end.
---

# PR Comment Sweep

Address actionable PR feedback from current branch PR, supplied PR number, or URL.

1. Standalone only: do not invoke, defer to, or modify Shipyard. Require authenticated `gh`; resolve an open PR with `gh pr view --json number,url,state,headRepository,headRefName,headRefOid,comments,reviews`. Require clean index and worktree; stop unless user explicitly adopts each pre-existing change. Require `HEAD` equals `headRefOid`; require branch equals PR head only when discovering current-branch PR, not for supplied number/URL. Fetch/reset only when explicitly authorized. Inspect status, base, and full diff; stop on non-open PR, missing PR, or ambiguous scope.
2. Fetch inline `reviewThreads` through paginated `gh api graphql`, including path, line, replies, `isResolved`, and `isOutdated`. Paginate replies too; never treat partial thread data as complete.
3. Ignore resolved, approval-only, informational, duplicate, and non-specific feedback. Re-anchor outdated threads against current code before marking them non-actionable. Assess each remaining item against code, callers, tests, and PR intent. Mark `actionable`, `non-actionable`, or `blocked`, with concise evidence.
4. State smallest proposed fix for each actionable item. Ask for approval before edits unless request explicitly authorizes end-to-end repair; then apply routine scoped proposals. Stop for conflicting feedback, unclear behavior, product choices, or scope expansion; never invent behavior.
5. Inspect full diff, run smallest relevant non-destructive validation, and stage only inspected paths. Stop on failed or unavailable required validation; do not commit or push without explicit risk acceptance. Do not change `.context/`, secrets, generated files, or unrelated work.
6. Commit scoped fixes with Conventional Commit message(s). Resolve PR `headRepository` as `OWNER/REPO`; select a configured remote by normalized GitHub host/owner/repo identity, accepting SSH and HTTPS forms. Push explicit `HEAD:<headRefName>` to it; stop before any push if none matches. Before resolving, re-fetch PR metadata and require `headRefOid` equals local `HEAD`; this also permits resolution without a new push when feedback is verified addressed at current head. Resolve only addressed review threads with `gh api graphql` `resolveReviewThread`.
7. Re-fetch full paginated feedback. Assess threads added during sweep before completion; resolve addressed threads and report pending/blockers for rest. Require every resolved thread reports `isResolved`. With no accepted fixes, make no commit or push. Do not reply unless explicitly requested. Report PR URL, actioned, resolved, skipped, pending feedback, validation, commit SHA(s), push result, and blockers.
