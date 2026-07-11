---
name: review-checkpoint
description: Run blocker-only Greptile branch reviews, with adversarial subagent fallback when Greptile is unavailable. Direct review requests are read-only; explicit fix loops and coordinating workflows may apply deterministic in-scope fixes.
---

# review-checkpoint

## Goal

Use Greptile first as a branch-diff review gate. If Greptile is unavailable, use subagent adversarial review. Review without changing code unless an explicit fix loop or coordinating workflow authorizes deterministic, in-scope fixes.

## Memory Boundary

- When the user invokes `review-checkpoint` directly, call `$agent-memory load` before `Before review` and `$agent-memory distill` as the final guard before every `PASS`, `BLOCKED`, or `PENDING_REVIEW` return.
- When a caller such as `issue-workbench` or Shipyard owns the memory boundary, skip both calls and preserve `.context/decisions.jsonl` for that caller.
- Capture only an accepted durable review rule or reusable root cause. Do not capture findings, review IDs, check state, or transient tooling failures.
- Memory failure must not change the review status.

## Inputs

- `mode` is optional; supported values are `review_only` and `fix_loop`.
- Direct review or run-Greptile requests default to `review_only`. Explicit apply/fix-loop requests and coordinating callers such as `issue-workbench` or Shipyard default to `fix_loop` unless they select `review_only`.
- `max_iterations` is optional and defaults to `3`.
- `review_base` is optional; use the caller-provided base ref when known.
- `wait_mode` is optional and defaults to `block`; supported values are `block` and `defer`.
- Use `defer` only when the user or coordinating skill explicitly asks to start a review and resume later.
- `poll_interval_seconds` is optional and defaults to `300`; in `defer` mode it sets `poll_after_utc`, and in `block` mode it is the sleep duration.
- `max_review_wait_minutes` is optional and defaults to `30`; in `block` mode, stop with `PENDING_REVIEW` when this wait budget is spent.
- `manifest_path` is optional. When provided, write pending review state, fallback review events, and final review status into that shipyard manifest instead of making `.context/progress.md` the source of truth.

## Rules

- Do not start a new review just to poll. Poll the same review ID.
- Classify every finding before acting:
  - `spec_blocker`: violates explicit issue/spec acceptance or adds unrequested behavior.
  - `standards_blocker`: violates repo instructions, local patterns, or maintainability baseline.
  - `safety_blocker`: risks data loss, secrets, security, or forbidden paths.
  - `test_blocker`: changed behavior lacks a meaningful validation path or has misleading tests.
  - `non_actionable`: cosmetic, speculative, stale, broad cleanup, unclear, contradictory, or outside scope.
- A finding is review-actionable only when it is a deterministic `spec_blocker`, `standards_blocker`, `safety_blocker`, or `test_blocker` in the branch diff, in scope, and fixable without a product decision. Classify broad cleanup, optional improvements, unclear requests, and anything outside the branch diff as `non_actionable`.
- In `review_only`, never edit files or commit fixes. In `fix_loop`, fix only review-actionable findings and record but do not fix `non_actionable` findings.
- If Greptile is unavailable, use one subagent adversarial branch-diff review as the review gate instead of stopping.
- Keep `.context/progress.md` local and uncommitted if used for pending review state.
- When `manifest_path` is provided, record review state there and keep `.context/progress.md` as a pointer to the manifest.
- Write fallback review payloads and large diffs only when the reviewer cannot reproduce them from git. Use one overwriteable `.context/review-payload.txt` and record its path and SHA in the manifest or progress pointer.
- If review history must survive handoff, append to one `.context/review-events.jsonl`; do not create per-review artifact folders.
- Keep `.context/progress.md` to five fields: `goal`, `current_step`, `artifacts`, `blockers`, and `validation`.
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

On resume, if `manifest_path` contains a pending Greptile review, run `git fetch --all --prune`, compare its branch, local HEAD SHA, upstream SHA, and known base SHA with current `git branch --show-current`, `git rev-parse HEAD`, `git rev-parse @{upstream}`, and `git rev-parse <review_base>`, then poll that review ID only when recorded values match and current UTC is at or after its poll-after time. If no `manifest_path` is provided, use the same rule with pending state in `.context/progress.md`. If the poll-after time has not arrived, return `PENDING_REVIEW`. If any value differs, or if `base_ref` or `base_sha` is unknown, mark the pending review `stale` with the reason and start a new review after resolving the base.

If the `greptile` command is missing, cannot start or show a review because of auth/service/plan availability, or returns no review ID, do not install or repair Greptile unless the user asked. Record the tooling error and run exactly one fallback review for that iteration. If fallback subagent capacity is unavailable, stop with `BLOCKED` unless the caller policy explicitly allows a local blocker-only review.

## Fallback

When Greptile is unavailable, delegate one adversarial review to a subagent:

- Use a prompt that includes `working_directory=<absolute path>` as the first field.
- Collect the exact review payload yourself: `git branch --show-current`, review base if known, changed files, `git diff --stat <base>...HEAD`, `git diff <base>...HEAD`, and validation commands/results.
- Prefer reproducible git references over files. If a file payload is required, overwrite `.context/review-payload.txt` and record that absolute path under `manifest_path` or `.context/progress.md` `artifacts`.
- Classify its output with the same review-actionable blocker rules as Greptile.
- Close the completed subagent after collecting its result.

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

If still running and `wait_mode=defer`, write pending state to the manifest when `manifest_path` is provided; otherwise write it to `.context/progress.md`. Return `PENDING_REVIEW` instead of sleeping. Keep `.context/progress.md` as a five-field pointer when a manifest is present; otherwise put the pending review object under `artifacts.pending_review` with at least:

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
