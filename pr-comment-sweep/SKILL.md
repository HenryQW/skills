---
name: pr-comment-sweep
description: Fetch GitHub pull request comments with gh, assess actionable feedback, then apply, validate, commit, push, and resolve scoped fixes without approval pauses. Use when asked to sweep, address, or fix PR comments end to end.
---

# PR Comment Sweep

Address actionable feedback on current-branch PR or supplied PR number/URL. Run
standalone; never invoke, defer to, or modify Shipyard.

1. Set `SNAPSHOT` to a temporary JSON path. Run `node scripts/pr-feedback.mjs fetch --pr "$PR" --out "$SNAPSHOT"`.
   Omit `--pr` only for current-branch discovery, then use snapshot's
   `pullRequest.url` as `$PR`. It requires authenticated `gh`, clean index/worktree,
   open PR, and local `HEAD == headRefOid`; discovery also
   requires matching branch. Inspect PR status, base, full diff, and snapshot. On
   mismatch, stop unless user says exact words **“Adopt PR head”**. Inspect `gh pr
   view "$PR" --json headRepository,headRefName`; select exactly one configured
   remote whose normalized GitHub host/owner/repo matches `headRepository`; run
   `git fetch "$REMOTE" "$HEAD_REF"`, then show `git log --oneline
   HEAD..FETCH_HEAD` and `git diff --stat HEAD..FETCH_HEAD`; require `git
   merge-base --is-ancestor HEAD FETCH_HEAD`, then run `git merge --ff-only
   FETCH_HEAD`. Stop on divergence; never hard-reset from “adopt”. Re-run fetch.
2. Fetcher paginates conversation comments, reviews, review threads, and every
   reply; cursor failure is blocked. Keep complete raw data only in temporary JSON.
   Console shows counts, new review IDs, unresolved thread bodies, and resolved IDs.
   Ignore resolved, approval-only, informational, duplicate, and non-specific
   feedback. Re-anchor outdated threads. Before edits, ledger every remaining item:

   | thread | verdict | evidence | smallest fix | regression |
   | --- | --- | --- | --- | --- |

   Verdict is `actionable`, `non-actionable`, or `blocked`, backed by code, callers,
   tests, and PR intent. Never reconstruct GraphQL pagination.
3. If feedback crosses SDK/framework boundary, inspect installed types and runtime
   caller before edit. Missing public capability is `blocked`; never type-cast or
   private-API hack. Invocation authorizes routine scoped edits, commits, push, and
   addressed-thread resolution. State ledger's smallest fix and proceed. Stop only
   for unclear scope/behavior, conflicting feedback, material product choice, or
   required scope expansion; never invent behavior.
4. Inspect full resulting diff and run smallest relevant non-destructive
   validation. Stage only inspected paths. Stop on failed or unavailable required
   validation unless user accepts risk. Never change `.context/`, secrets,
   generated files, or unrelated work. Never wait or poll for GitHub checks; do
   not use `gh pr checks --watch` (including interval variants). Report pending
   checks and leave CI repair to its owning workflow.
5. Commit accepted fixes with scoped Conventional Commit message(s). With no fixes,
   make no commit or push. After clean-worktree validation, run `node scripts/pr-feedback.mjs push --snapshot "$SNAPSHOT"`. It selects one matching PR-head remote, pushes explicit `HEAD:<headRefName>`, and verifies remote `headRefOid == local HEAD`.
6. Run `node scripts/pr-feedback.mjs fetch --pr "$PR" --out "$FINAL_SNAPSHOT"`.
   Assess feedback added during sweep, then pass only ledger-addressed IDs: `node scripts/pr-feedback.mjs resolve --pr "$PR" --expected-head "$(git rev-parse HEAD)" --thread "$ID"`; repeat `--thread` per ID. It rechecks open PR and exact head,
   then verifies every supplied ID is resolved. Re-fetch full feedback once more,
   assess late feedback, and resolve only newly addressed IDs. Do not reply unless
   explicitly requested.
7. Report PR URL, actioned, resolved, skipped, pending/blockers, validation, commit
   SHA(s), and push result.
