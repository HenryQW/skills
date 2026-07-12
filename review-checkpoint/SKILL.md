---
name: review-checkpoint
description: Run blocker-only Greptile branch reviews, with adversarial subagent fallback when Greptile is unavailable. Direct review requests are read-only; explicit fix loops and coordinating workflows may apply deterministic in-scope fixes.
---

# review-checkpoint

## Goal

Use Greptile first as a branch-diff review gate. If Greptile is unavailable, use subagent adversarial review. Review without changing code unless an explicit fix loop or coordinating workflow authorizes deterministic, in-scope fixes.

## Memory Boundary

- Direct invocation calls `$agent-memory load` before `Before review` and
  `$agent-memory distill` before every `PASS`, `BLOCKED`, or `PENDING_REVIEW`.
- Under `issue-workbench` or Shipyard, skip both calls and preserve
  `.context/decisions.jsonl` for the caller. Capture only accepted durable
  review rules or reusable root causes; memory failure never changes status.

## Inputs

- `mode`: `review_only` or `fix_loop`; direct review defaults to `review_only`,
  while explicit apply/fix-loop and coordinating callers default to `fix_loop`.
- `max_iterations`: optional, default `3`.
- `review_base` is optional; use the caller-provided base ref when known.
- `wait_mode`: `block` (default) or `defer`; use `defer` only when explicitly
  asked to start now and resume later. `poll_interval_seconds` defaults to 300;
  it sets `poll_after_utc` when deferred and sleep duration when blocking.
- `max_review_wait_minutes`: optional, default 30; blocking returns
  `PENDING_REVIEW` when spent.
- `manifest_path`: optional and only for Shipyard's integration review. Child
  Issue Workbench reviews retain isolated-worktree state in their handoffs.

## Rules

- Do not start a new review just to poll. Poll the same review ID.
- Classify findings as `spec_blocker` (explicit acceptance or unrequested
  behavior), `standards_blocker` (repo or local standards), `safety_blocker`
  (data, secrets, security, or forbidden paths), `test_blocker` (missing or
  misleading validation), or `non_actionable` (cosmetic, speculative, stale,
  broad, unclear, contradictory, or out of scope).
- Only deterministic in-scope blockers fixable without a product decision are
  review-actionable; all others are `non_actionable`.
- In `review_only`, never edit files or commit fixes. In `fix_loop`, fix only review-actionable findings and record but do not fix `non_actionable` findings.
- If Greptile is unavailable, use one subagent adversarial branch-diff review as the review gate instead of stopping.
- Keep pending `.context/progress.md` local and uncommitted, with only `goal`,
  `current_step`, `artifacts`, `blockers`, and `validation`. With
  `manifest_path`, record state in the manifest and use progress as its pointer.
- Write fallback payloads or large diffs only when git cannot reproduce them:
  overwrite `.context/review-payload.txt` and record its path and SHA. Append
  handoff history to `.context/review-events.jsonl`; do not create folders.
- Each fix iteration must resolve or reduce the deterministic blocker set.
- Do not start another review loop for `non_actionable` findings.
- Stop if the same finding repeats after a targeted fix, contradicts a prior accepted finding, or if the iteration budget is spent.
- Mark contradictory repeat findings as `non_actionable: contradictory semantics`; record the reason and do not keep fixing.

## Before review

Run:

```bash
git status --short
```

Start Greptile only from a clean working tree. `.context/progress.md` may remain uncommitted.

Before starting Greptile, ensure remote state matches local HEAD because Greptile reviews the pushed branch:

```bash
git rev-parse --abbrev-ref --symbolic-full-name @{upstream}
git rev-parse HEAD
git rev-parse @{upstream}
```

If no upstream exists, run `git push --set-upstream origin HEAD`. If `HEAD` differs from `@{upstream}`, run `git push`. Re-run the three commands above and start Greptile only when `git rev-parse HEAD` equals `git rev-parse @{upstream}`.

On resume, `git fetch --all --prune`; read pending state from `manifest_path` or
`.context/progress.md`, and compare its branch, local HEAD, upstream, and base
SHAs with current git values. Poll that ID only when all match and UTC is at or
after `poll_after_utc`; otherwise return `PENDING_REVIEW` before that time, or
mark it `stale` (including unknown `base_ref` or `base_sha`) and resolve the
base before a new review.

If the `greptile` command is missing, cannot start or show a review because of auth/service/plan availability, or returns no review ID, do not install or repair Greptile unless the user asked. Record the tooling error and run exactly one fallback review for that iteration. If fallback subagent capacity is unavailable, stop with `BLOCKED` unless the caller policy explicitly allows a local blocker-only review.

## Fallback

When Greptile is unavailable, delegate one adversarial review to a subagent:

- Put `working_directory=<absolute path>` first. Collect the exact git and
  validation payload in the template below; prefer reproducible refs, using
  `.context/review-payload.txt` only when required. Classify output by the same
  blocker rules and close the subagent after collecting its result.

Prompt template:

```text
working_directory=<absolute path>
review_base=<base ref or unknown>
branch=<branch>
changed_files=<files>
diff_stat=<short captured stat>
diff_artifact=<absolute path>
payload_artifact=<absolute path>
verification_artifact=<absolute path or short commands/results>

Review only the artifact paths above. Do not inspect another worktree. Do not edit files, commit, push, or review broad cleanup. Classify each finding as `spec_blocker`, `standards_blocker`, `safety_blocker`, `test_blocker`, or `non_actionable`. Report only deterministic in-scope blockers with file/line evidence, plus any `non_actionable` findings that explain why they were not fixed, or PASS.
```

Treat the completed subagent review as the current review output. If fixes are committed and Greptile is still unavailable, run at most one fallback subagent review for the next iteration.

## Loop

Run one completed review in `review_only`; repeat up to `max_iterations` in `fix_loop`:

```bash
greptile review --agent
```

Record the review ID. If none is returned, use the fallback.

```bash
greptile review show <review_id> --agent
```

If still running with `wait_mode=defer`, write pending state to the manifest or
progress file, return `PENDING_REVIEW` without sleeping, and use progress only
as the five-field manifest pointer. Without a manifest, put this under
`artifacts.pending_review`:

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

Set `poll_after_utc` from a Greptile retry time when provided; otherwise use current UTC plus `poll_interval_seconds`.

If still running and `wait_mode=block`, wait the configured `poll_interval_seconds` exactly and run the same `show` command again until complete, `max_review_wait_minutes` is spent, or the latest completed review has no review-actionable blockers. Do not poll at a hardcoded 30-second interval unless the caller configured `poll_interval_seconds=30`.

When blocking on a current PR or current branch and the user did not explicitly request `defer`, do not return `PENDING_REVIEW` until `max_review_wait_minutes` is spent.

If `show` fails because Greptile is unavailable, use the fallback.

When `manifest_path` is provided, record each pending, fallback, pass, fail, timeout, or blocker event with:

```bash
review_event_file=$(mktemp)
# write the review event JSON object to "$review_event_file"
python3 <shipyard_dir>/scripts/manifest.py --manifest <manifest_path> set-review --file "$review_event_file"
```

Every passing integration event must include `status:"PASS"`, the current `branch`, `base_sha`, and exact reviewed `head_sha`. Resolve both SHAs from git after the review completes, and do not return `PASS` unless `set-review` accepts the event.

Classify blockers from the full `show` output.

If no review-actionable blockers remain, stop.

If `mode=review_only` and review-actionable blockers remain, return `BLOCKED` with those findings without editing or committing.

If a finding repeats after a targeted fix but now asks for the opposite behavior, classify it as `non_actionable: contradictory semantics`, record both review IDs, and stop fixing that finding.

Fix the smallest set of files needed for review-actionable blockers, then inspect and validate:

```bash
git status --short
git diff --stat
git diff
```

Run the smallest relevant local check. If none is obvious, do not invent one.

Commit only inspected files:

```bash
git add <files>
git commit -m "fix(scope): address greptile review"
```

Start a new Greptile review, or fallback subagent review when Greptile is still unavailable, only after committing fixes for review-actionable blockers. Before every new Greptile review, including fix-loop iterations, repeat the pushed-head synchronization check in `Before review` and proceed only when local `HEAD` equals its upstream. The final gate is the latest completed review with no later commit.

## Output

Report `mode`, review IDs or fallback reviews, checks run, final status, and unresolved review-actionable blockers if any. For deferred reviews or block-mode wait timeout, return `PENDING_REVIEW` with the pending review state location.
