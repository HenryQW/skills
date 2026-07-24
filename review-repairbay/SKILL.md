---
name: review-repairbay
description: Inspect or address actionable GitHub pull request review feedback. Use when the user wants to inspect unresolved review threads, fix selected feedback, or clear all actionable comments on a PR. Use `gh` and the bundled GraphQL script whenever thread-level state, resolution status, or inline review context matters.
---

# Review Repairbay

Use thread-aware GraphQL data when review state matters; flat comments are not a
complete thread model.

## Memory

Direct entry loads memory only when feedback depends on prior project decisions.
Evidence-complete routine fixes skip it; `inspect-only` and nested invocation
defer it to the caller. Capture durable review decisions, repository rules, or
reusable root causes—not comments, thread state, IDs, or routine fixes.

## Workflow

1. Select intent: `inspect-only` reads and reports; `fix-selected` changes only
   supplied feedback and asks for selection when absent; `clear-all` authorizes
   scoped local fixes plus required thread replies and resolutions.
2. Feedback is evidence-complete when it names the file or symbol, defect, and
   expected behavior. Then `fix-selected` skips PR/thread discovery: inspect the
   named code, direct callers, and regression tests; make the smallest fix and run
   focused validation. Direct mode then runs any required broader validation;
   nested Shipyard mode leaves `final_check` to Shipyard. Escalate only when
   evidence is contradicted or insufficient. Direct fixes remain uncommitted
   and unpushed unless the user requested publication. When nested Shipyard explicitly
   delegates commit-and-push authority, inspect the final scoped code diff,
   commit only those fixes, and push before returning; nesting alone is not
   authority. `fix-selected` never authorizes GitHub thread writes.
3. Otherwise derive repo and PR from a URL, require `--repo` with a number, or
   resolve the current branch. When discovery, inline context, replies, or
   resolution matter, run:

   ```bash
   python "<skill>/scripts/fetch_comments.py" --repo OWNER/REPO --pr NUMBER
   ```

4. Group by file or behavior; exclude informational, approved, resolved,
   outdated, and duplicate threads. Keep changes traceable and ask only about
   ambiguity, conflicts, or material product decisions.
5. Only explicit `clear-all` authorizes replies and resolutions. Reply/resolve
   each addressed actionable thread and re-fetch until unresolved actionable
   count is zero. No other mode or nested caller implies thread-write authority;
   submitting a review or unrelated external write still requires explicit
   authorization.

Finish with:

```text
status=PASS|BLOCKED|PENDING artifacts=<path-or-none> summary=<one line>
```

`PASS` means the selected mode is complete and validated; `clear-all` also
requires the zero-thread re-fetch. `BLOCKED` means ambiguity, conflict, product
decision, missing scope, or unavailable GitHub access. `PENDING` means a
requested write or re-fetch is active. Do not print raw diffs or repeated
progress; on auth or rate limits, request reauthentication and retry.
