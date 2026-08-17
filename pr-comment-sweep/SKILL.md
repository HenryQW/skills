---
name: pr-comment-sweep
description: Fetch GitHub pull request comments with gh, assess actionable feedback, then apply, validate, commit, push, and resolve scoped fixes without approval pauses. Use when asked to sweep, address, or fix PR comments end to end.
---

# PR Comment Sweep

Address actionable feedback on current-branch PR or supplied PR number/URL. Run
standalone; never invoke, defer to, or modify Shipyard.

1. Resolve `<skill>` to installed `pr-comment-sweep` directory. Set optional `$PR` number/URL. Inspect `git status`. On documented resume, verify ignored `.context/progress.md` matches PR, local `HEAD`, snapshot, completed phase, and exact owned dirty paths; skip completed clean-only steps and continue at its next phase. Otherwise require a clean tree and stop rather than absorb unknown changes. For a fresh start, run:

   ```bash
   SNAPSHOT=$(mktemp)
   if [ -n "${PR:-}" ]; then
     "<skill>/scripts/verify-pr-target.sh" "$PR"
     node "<skill>/scripts/pr-feedback.mjs" fetch --pr "$PR" --out "$SNAPSHOT"
   else
     "<skill>/scripts/verify-pr-target.sh"
     node "<skill>/scripts/pr-feedback.mjs" fetch --out "$SNAPSHOT"
   fi
   PR=$(jq -r '.pullRequest.url' "$SNAPSHOT")
   ```

   Verifier requires authenticated `gh`, open PR, clean index/worktree, matching local `HEAD`, and exactly one matching HTTPS/SSH push remote. On head mismatch, stop unless user says exact words **“Adopt PR head”**. Inspect `gh pr view "$PR" --json headRepository,headRefName`; select exactly one configured remote whose normalized GitHub host/owner/repo matches `headRepository`; run `git fetch "$REMOTE" "$HEAD_REF"`, show `git log --oneline HEAD..FETCH_HEAD` and `git diff --stat HEAD..FETCH_HEAD`, require `git merge-base --is-ancestor HEAD FETCH_HEAD`, then run `git merge --ff-only FETCH_HEAD`. Stop on divergence; never hard-reset from “adopt”. Re-run verification and fetch. Inspect base, full diff, and snapshot. Project-required ignored `.context/progress.md` is the sole `.context/` exception: record PR, snapshots, expected SHA, ledger, validation, commit, push, and resolved IDs; never stage it.
2. Fetcher paginates conversation comments, reviews, review threads, and every reply;
   it retries read-only TLS/5xx failures only. Snapshot keeps full raw JSON; terminal
   output shows conversation comments, review bodies, all unresolved current/outdated
   threads with full replies, status, new review IDs, and resolved IDs. Follow
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
   user accepts risk. Never change secrets or unrelated work. Never hand-edit generated
   files; change source, run the repository's canonical generator for required tracked
   artifacts, then inspect and stage both. Never wait or poll GitHub checks; report
   pending checks and leave CI repair to its owning workflow.
5. Commit accepted fixes with scoped Conventional Commit message(s). With no fixes,
   make no commit or push. After clean-worktree validation, run `node "<skill>/scripts/pr-feedback.mjs" push --snapshot "$SNAPSHOT"`. It selects one matching
   PR-head remote, pushes explicit `HEAD:<headRefName>` once, and accepts only exact
   local-head confirmation, including already-pushed and ambiguous-error recovery.
6. Set `FINAL_SNAPSHOT=$(mktemp)`; copy the baseline with `cp "$SNAPSHOT" "$FINAL_SNAPSHOT"`, then run `node "<skill>/scripts/pr-feedback.mjs" fetch --pr "$PR" --out "$FINAL_SNAPSHOT"`.
   Assess added feedback, then resolve all addressed IDs in one invocation: `node "<skill>/scripts/pr-feedback.mjs" resolve --pr "$PR" --expected-head "$(git rev-parse HEAD)" --thread "$ID1" --thread "$ID2"`; repeat the flag, not the command, for more IDs. It checks open PR and exact head, issues no retried mutation, and verifies every supplied ID resolved. Never resolve non-actionable or blocked threads; report them pending. Re-fetch into the same final snapshot once, assess late feedback, and resolve newly addressed IDs in one batch. Run `node "<skill>/scripts/pr-feedback.mjs" checks --pr "$PR"` once for final merge/check status; bounded transient read retries are allowed, polling is not. Do not reply unless explicitly requested.
7. Report:

   ```text
   PR | actioned | resolved IDs | skipped IDs | pending IDs | checks | commits | push |
   blockers
   ```
