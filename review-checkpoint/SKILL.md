---
name: review-checkpoint
description: Run blocker-only Greptile branch reviews, with adversarial subagent fallback when Greptile is unavailable. Direct review requests are read-only; explicit fix loops and coordinating workflows may apply deterministic in-scope fixes.
---

# Review Checkpoint

Use Greptile as the branch-diff gate. Review is read-only unless `fix_loop` is explicitly authorized or selected by a coordinating workflow.

## Inputs

- `mode`: `review_only` (direct default) or `fix_loop` (explicit fix/coordinator default).
- `max_iterations`: default `3`.
- `review_base`: optional caller-provided base ref.
- `wait_mode`: `block` (default) or explicitly requested `defer`.
- `poll_interval_seconds`: default `300`; sets only deferred `poll_after_utc`.
- `max_review_wait_minutes`: default `30`; a spent blocking wait returns `PENDING_REVIEW`.
- `manifest_path`: optional and only for Shipyard's integration review; child reviews keep isolated state in their handoffs.

## Memory

Direct invocation owns `$agent-memory load` and distillation before every terminal status. Nested Workbench or Shipyard invocation skips both and preserves `.context/decisions.jsonl`. Capture only accepted durable review rules or reusable root causes; memory failure does not change status.

## Findings and authorization

- Classify findings as `spec_blocker` (acceptance or unrequested behavior), `standards_blocker` (repository rules), `safety_blocker` (data, secrets, security, or forbidden paths), `test_blocker` (missing or misleading validation), or `non_actionable`.
- A blocker is actionable only when deterministic, in scope, and fixable without a product decision. Cosmetic, speculative, stale, broad, unclear, contradictory, or out-of-scope findings are `non_actionable`.
- `review_only` never edits. `fix_loop` fixes only actionable findings and each iteration must reduce that set. Do not loop on non-actionable findings.
- Stop when the budget is spent, a finding repeats after its targeted fix, or a later finding contradicts an accepted one. Record contradiction as `non_actionable: contradictory semantics` with both review IDs.

## Review state machine

1. Require a clean worktree except local `.context/progress.md`. Resolve `review_base`; ensure the branch has an upstream and local `HEAD` equals the pushed upstream before every new review.
2. On resume, fetch and compare saved branch, local HEAD, upstream, base ref, and base SHA with Git. Before `poll_after_utc`, matching state returns `PENDING_REVIEW` without invoking Greptile. Mark mismatches or unknown base values stale and resolve them, but never replace the review ID for unchanged `HEAD`.
3. For a new `HEAD`, start exactly one process and record its review ID when emitted:

   ```bash
   greptile review --agent
   ```

   - `block`: await that same process to terminal output or `max_review_wait_minutes`; never start `review show` while it is live.
   - `defer`: after obtaining an incomplete review ID, stop and reap the local stream, persist pending state, and return `PENDING_REVIEW` without sleeping or starting `show`.
   - Timeout after an ID reaps only the local process, retains the remote ID, persists it, and returns `PENDING_REVIEW`.
4. At or after `poll_after_utc`, resume the saved ID with exactly one process:

   ```bash
   greptile review show <review_id> --agent
   ```

   Await that same process. In block mode, use `max_review_wait_minutes`; in defer mode, reap an incomplete process and advance `poll_after_utc`. Timeout or `show` failure retains the same ID and returns `PENDING_REVIEW`; never run another concurrent `show`, fallback, or replacement review for unchanged `HEAD`.
5. A new review ID is allowed only after an actionable fix creates and pushes a new commit. The final gate is the latest completed review with no later commit.

`poll_interval_seconds` never drives blocking polls. Report state changes only; any host heartbeat must await the same process without launching a command or repeating detailed status.

## Pending state

Without a manifest, store this under `.context/progress.md` `artifacts.pending_review`:

```text
review_id=<review id>
branch=<branch>
local_head_sha=<git rev-parse HEAD>
upstream_sha=<git rev-parse @{upstream}>
base_ref=<review_base or unknown>
base_sha=<git rev-parse <review_base> or unknown>
poll_after_utc=<YYYY-MM-DDTHH:MM:SSZ>
progress_path=<absolute path to .context/progress.md>
```

Keep progress local and limited to `goal`, `current_step`, `artifacts`, `blockers`, and `validation`. With `manifest_path`, record canonical state in the manifest and use progress only as its pointer.

## Fallback

If Greptile is missing, unavailable, or exits before yielding an ID, record the tool error and run exactly one read-only adversarial subagent review for that iteration. Give it the absolute worktree, base, branch, reproducible diff refs or artifact, and validation evidence; require the same blocker taxonomy and file/line evidence. If no reviewer is available, return `BLOCKED` unless caller policy explicitly permits a local review. Once an ID exists, local process failure or timeout never triggers fallback.

Store a diff payload only when Git cannot reproduce it, overwriting `.context/review-payload.txt` and recording its path and SHA; append review history to `.context/review-events.jsonl` without per-review folders.

## Complete or fix

- No actionable blocker -> `PASS`.
- Actionable blockers in `review_only` -> `BLOCKED` with findings and no edits.
- In `fix_loop`, apply the smallest fix, inspect the diff, run the smallest relevant check, commit inspected files, push, and return to Step 1 for the new `HEAD`.

When `manifest_path` is set, record pending, fallback, pass, fail, timeout, and blocker events through:

```bash
python3 <shipyard_dir>/scripts/manifest.py --manifest <manifest_path> set-review --file <event_file>
```

A passing integration event must contain `status:"PASS"`, current `branch`, `base_sha`, and exact reviewed `head_sha`; return `PASS` only after the manifest accepts it.

## Output

Return `PASS`, `BLOCKED`, or `PENDING_REVIEW` with mode, review IDs or fallback, checks, unresolved actionable blockers, and the pending-state path when applicable.
