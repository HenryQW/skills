---
name: pr-comment-sweep
description: Fetch GitHub pull request comments with gh, assess actionable feedback, then apply, validate, commit, push, and resolve scoped fixes without approval pauses. Use when asked to sweep, address, or fix PR comments end to end.
---

# PR Comment Sweep

Address actionable feedback on current-branch PR or supplied PR number/URL.
Run standalone; never invoke, defer to, or modify Shipyard.

1. Resolve `<skill>`, set optional `$PR`, and require a clean tracked tree. On
   resume, dirt, or head mismatch, read [Sweep recovery](references/recovery.md)
   and stop unless its checkpoint or adoption rules pass. For a fresh sweep:

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

   Verifier requires authenticated `gh`, open PR, exact local/PR head, and one
   matching push remote. Inspect base, full diff, and raw snapshot. Maintain
   recovery reference's one-line checkpoint after each phase.
2. Initial fetch prints all conversation comments, review bodies, unresolved
   current/outdated threads, replies, and status. Later fetches into a copied
   snapshot print additions, edits, and state changes only; raw JSON remains complete.
   Follow [Thread triage](references/thread-triage.md) and ledger every item as
   `actionable`, `non-actionable`, or `blocked`, with evidence, smallest fix,
   and regression. Never reconstruct GraphQL pagination.
3. Verify feedback against code, callers, tests, and PR intent. For SDK/framework
   claims, inspect installed types and runtime caller; missing public capability
   is `blocked`, never a private-API or cast workaround. Invocation authorizes
   scoped edits, commits, push, and addressed-thread resolution. Stop only for
   unclear behavior, conflicting feedback, material product choice, or scope
   expansion.
4. Inspect resulting diff and run smallest relevant non-destructive validation.
   Stage only inspected paths; stop on failed or unavailable required validation
   unless user accepts risk. Never change secrets or unrelated work. Never
   hand-edit generated files: change source, run canonical generator for required
   tracked artifacts, then inspect both. Never wait or poll checks.
5. Commit accepted fixes with scoped Conventional Commit message(s). With no
   fixes, do not commit or push. After clean-tree validation, run
   `node "<skill>/scripts/pr-feedback.mjs" push --snapshot "$SNAPSHOT"`; helper
   pushes once and accepts only exact local-head confirmation.
6. Copy baseline before final fetch:

   ```bash
   FINAL_SNAPSHOT=$(mktemp)
   cp "$SNAPSHOT" "$FINAL_SNAPSHOT"
   node "<skill>/scripts/pr-feedback.mjs" fetch --pr "$PR" --out "$FINAL_SNAPSHOT"
   ```

   Assess delta, then resolve all addressed IDs in one command, repeating flag:
   `node "<skill>/scripts/pr-feedback.mjs" resolve --pr "$PR" --expected-head
   "$(git rev-parse HEAD)" --thread "$ID1" --thread "$ID2"`. Never resolve
   non-actionable or blocked threads. Re-fetch once into `FINAL_SNAPSHOT`, assess
   late delta, batch any newly addressed IDs, then run
   `node "<skill>/scripts/pr-feedback.mjs" checks --pr "$PR"` once. Read-only
   transient retries are allowed; mutation retries and polling are not. Do not
   reply unless explicitly requested.
7. Report `PR | actioned | resolved IDs | skipped IDs | pending IDs | checks |
   commits | push | blockers`.
