---
name: pr-comment-sweep
description: Fetch GitHub pull request comments with gh, assess actionable feedback, then apply, validate, commit, push, and resolve scoped fixes without approval pauses. Use when asked to sweep, address, or fix PR comments end to end.
---

# PR Comment Sweep

Address actionable feedback on current-branch PR or supplied PR number/URL. Run
standalone; never invoke, defer to, or modify Shipyard.

1. Set `$PR` and temporary `$SNAPSHOT`. Run `scripts/verify-pr-target.sh "$PR"`;
   it requires authenticated `gh`, open PR, clean index/worktree, matching local
   `HEAD`, and exactly one matching HTTPS/SSH push remote. Then use read-only flow:

   ```bash
   scripts/fetch-pr-feedback.py "$PR" > "$SNAPSHOT"
   jq '.openCurrentThreads' "$SNAPSHOT"
   ```

   For compact terminal output instead, run `node scripts/pr-feedback.mjs fetch --pr "$PR" --out "$SNAPSHOT"`. On head mismatch, stop unless user says exact words **“Adopt PR head”**. Inspect `gh pr view "$PR" --json headRepository,headRefName`; select exactly one configured remote whose normalized GitHub host/owner/repo matches `headRepository`; run `git fetch "$REMOTE" "$HEAD_REF"`, show `git log --oneline HEAD..FETCH_HEAD` and `git diff --stat HEAD..FETCH_HEAD`, require `git merge-base --is-ancestor HEAD FETCH_HEAD`, then
   run `git merge --ff-only FETCH_HEAD`. Stop on divergence; never hard-reset from
   “adopt”. Re-run verification and fetch. Inspect PR status, base, full diff, and
   snapshot.
2. Fetcher paginates conversation comments, reviews, review threads, and every reply;
   it retries read-only TLS/5xx failures only. Snapshot keeps full raw JSON; compact
   output shows only open/current bodies, new review IDs, and resolved IDs. Follow
   [Thread triage](references/thread-triage.md). Before edits, ledger every remaining
   item:

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
4. Inspect full resulting diff and run smallest relevant non-destructive validation.
   Stage only inspected paths. Stop on failed or unavailable required validation unless
   user accepts risk. Never change `.context/`, secrets, generated files, or unrelated
   work. Never wait or poll GitHub checks; report pending checks and leave CI repair to
   its owning workflow.
5. Commit accepted fixes with scoped Conventional Commit message(s). With no fixes,
   make no commit or push. After clean-worktree validation, run `node scripts/pr-feedback.mjs push --snapshot "$SNAPSHOT"`. It selects one matching
   PR-head remote, pushes explicit `HEAD:<headRefName>`, and verifies remote
   `headRefOid == local HEAD`.
6. Run `node scripts/pr-feedback.mjs fetch --pr "$PR" --out "$FINAL_SNAPSHOT"`.
   Assess added feedback, then pass only addressed IDs: `node scripts/pr-feedback.mjs resolve --pr "$PR" --expected-head "$(git rev-parse HEAD)" --thread "$ID"`;
   repeat `--thread` per ID. It checks open PR and exact head, issues no retried
   mutation, and verifies every supplied ID resolved. Never resolve non-actionable or
   blocked threads; report them pending. Re-fetch full feedback once more, assess late
   feedback, and resolve only newly addressed IDs. Do not reply unless explicitly
   requested.
7. Report:

   ```text
   PR | actioned | resolved IDs | skipped IDs | pending IDs | checks | commits | push |
   blockers
   ```
