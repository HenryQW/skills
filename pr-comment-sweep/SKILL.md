---
name: pr-comment-sweep
description: Fetch GitHub pull request comments with gh, assess actionable feedback, then apply, validate, commit, push, and resolve scoped fixes without approval pauses. Use when asked to sweep, address, or fix PR comments end to end.
---

# PR Comment Sweep

Address actionable feedback on current-branch PR or supplied PR number/URL. Run
standalone; never invoke, defer to, or modify Shipyard.

1. Run `scripts/fetch_feedback.py --output /tmp/pr-feedback.json`, adding `--pr URL`
   or `--repo OWNER/REPO --pr NUMBER` when supplied. Stop on its state, auth,
   cleanliness, branch, or head mismatch errors; fetch/reset only when explicitly
   authorized. Inspect PR status, base, full diff, and snapshot. See
   [GitHub operations](references/gh-operations.md) only for command details or
   recovery.
2. Ignore resolved, approval-only, informational, duplicate, and non-specific
   feedback. Re-anchor outdated threads against current code. Assess every other
   item against code, callers, tests, and PR intent as `actionable`,
   `non-actionable`, or `blocked`, with concise evidence.
3. Invocation authorizes routine scoped edits, commits, push, and addressed-thread
   resolution. State smallest fix and proceed. Stop only for unclear scope or
   behavior, conflicting feedback, material product choice, or required scope
   expansion; never invent behavior.
4. Inspect full resulting diff and run smallest relevant non-destructive
   validation. Stage only inspected paths. Stop on failed or unavailable required
   validation unless user accepts risk. Never change `.context/`, secrets,
   generated files, or unrelated work. Never wait or poll for GitHub checks; do
   not use `gh pr checks --watch` (including interval variants). Report pending
   checks and leave CI repair to its owning workflow.
5. Commit accepted fixes with scoped Conventional Commit message(s). With no fixes,
   make no commit or push. After clean-worktree validation, run
   `scripts/push_head.py --snapshot /tmp/pr-feedback.json`.
6. Re-run fetcher to `/tmp/pr-feedback-final.json`; assess feedback added during
   sweep. Pass only addressed review thread IDs to
   `scripts/resolve_threads.py --snapshot /tmp/pr-feedback-final.json ID...`.
   Re-fetch once more; require addressed IDs resolved and assess any late feedback.
   Do not reply unless explicitly requested.
7. Report PR URL, actioned, resolved, skipped, pending/blockers, validation, commit
   SHA(s), and push result.
