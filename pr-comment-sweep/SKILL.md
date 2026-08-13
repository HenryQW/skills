---
name: pr-comment-sweep
description: Fetch GitHub pull request comments with gh, assess actionable feedback, propose fixes, then apply, validate, commit, and push accepted fixes. Use when asked to sweep, address, or fix PR comments end to end.
---

# PR Comment Sweep

Address actionable PR feedback from current branch PR, supplied PR number, or URL.

1. Require authenticated `gh`; resolve PR, require checked-out branch equals PR head, then inspect status, base, and full diff. Stop on unrelated dirty changes, missing PR, or ambiguous scope.
2. Fetch conversation comments and reviews with `gh pr view --json`; fetch inline `reviewThreads` through paginated `gh api graphql`, including path, line, replies, `isResolved`, and `isOutdated`. Run `review-repairbay/scripts/fetch_comments.py` when available; otherwise use one paginated `gh api graphql` query.
3. Ignore resolved, outdated, approval-only, informational, duplicate, and non-specific feedback. Assess each remaining item against code, callers, tests, and PR intent. Mark `actionable`, `non-actionable`, or `blocked`, with concise evidence.
4. State smallest proposed fix for each actionable item. Ask for approval before edits unless request explicitly authorizes end-to-end repair; then apply routine scoped proposals. Stop for conflicting feedback, unclear behavior, product choices, or scope expansion; never invent behavior.
5. Inspect full diff, run smallest relevant non-destructive validation, and stage only inspected paths. Do not change `.context/`, secrets, generated files, or unrelated work.
6. Commit scoped fixes with Conventional Commit message(s), then push current PR branch. With no accepted fixes, make no commit or push. Do not reply to or resolve GitHub threads unless explicitly requested.
7. Report PR URL, actioned and skipped feedback, proposed/applied fixes, validation, commit SHA(s), push result, and blockers.
