---
name: gh-autopilot
description: Run a standalone autonomous GitHub Copilot pull request review loop with explicit stage entry and event logs. Use when Codex should start from a user-selected stage (create PR, monitor review, or address existing comments), execute deterministic cycle transitions, and continue looping until Copilot reports no comments or the cycle times out.
---

# GH Autopilot

Use this skill to operate a deterministic Copilot review loop on one PR.
The user must explicitly choose the starting stage. The skill must begin there
and keep looping until a terminal condition is reached.

This skill is stateful and persists artifacts under `.context/gh-autopilot/`.

## Required Start Stage

Require the user to provide one of the following stage values:

- `1` (`create_pr`): PR not created yet. Create/select PR first.
- `2` (`monitor_review`): PR exists and Copilot is reviewing (or expected soon).
- `3` (`address_comments`): Copilot comments already exist and must be addressed now.

If start stage is missing, ask once and wait. Do not guess.

Terminal end conditions for the loop:

- `completed_no_comments` (success)
- `timeout` (Copilot did not return in the per-cycle wait window)

## Timing Contract

- Initial wait: 300 seconds.
- Poll interval after initial wait: 45 seconds.
- Keep polling after 10 minutes.
- Stop each cycle wait at 40 minutes (2400 seconds) and mark timeout.
- Stop entire loop when Copilot summary says `generated no comments`.

## Primary Engine

Use `scripts/run_autopilot_loop.py` as the control-plane entrypoint.

### Commands

- `init`: initialize state for one PR.
- `run-cycle`: wait for new Copilot review and export cycle artifacts.
- `finalize-cycle`: mark current cycle addressed and re-request Copilot.
- `status`: print current state.
- `assert-drained`: fail if any address-required cycle is still pending.

### State File

Default: `.context/gh-autopilot/state.json`

Important fields:

- `status`
- `cycle`
- `last_processed_review_id`
- `pending_review_id`
- `pr`

### Event Log

Default: `.context/gh-autopilot/events.jsonl`

Each line is a JSON event with timestamp and payload.

### Context Workspace Files

Use `.context/gh-autopilot/` as the durable workspace for autonomy and recovery.

- `context.md`: single source of truth for next actions, status snapshot, artifacts, and suggested commands.

Keep this intentionally simple: one context file, not multiple overlapping notes.

## Stage Router

```text
Start Stage (user-selected)
   |
   +-- Stage 1: create_pr ----------+
   |                                |
   +-- Stage 2: monitor_review -----+--> run-cycle --> [terminal?] --> stop
   |                                |                     |
   +-- Stage 3: address_comments ---+                     +--> action required -> Stage 3
                                                             |
                                                             +--> finalize-cycle -> Stage 2
```

## Stage Details

### Stage 1 (`create_pr`)

User intent: PR has not been created yet.

Actions:

1. Run `gh auth status`.
2. Resolve current-branch PR with `gh pr view` (omit `--pr`).
3. If an open PR already exists for the branch, skip PR creation and move to Stage 2.
4. If no PR exists, run `gh-pr-creation` to open one.
5. Initialize state with `init` (avoid `--force` unless state is intentionally reset).
6. Move to Stage 2.

### Stage 2 (`monitor_review`)

User intent: PR exists and we are waiting for Copilot output.

Actions:

1. Run `gh auth status`.
2. Resolve PR (current branch or explicit `--pr`).
3. Ensure state exists for the PR:
   - If missing: run `init`.
   - If state already `awaiting_address` or `awaiting_triage`: move directly to Stage 3.
4. Run `run-cycle` with normal timing (`300/45/2400`).
   - `run-cycle` must export all Copilot comments for the active review cycle into `cycle.json`.
5. Interpret result:
   - `completed_no_comments` -> terminal success; stop loop.
     - includes cycles where no Copilot thread comments were captured for that review round
   - `timeout` -> terminal timeout; stop loop.
   - `awaiting_address` or `awaiting_triage` -> move to Stage 3.
6. Before any terminal stop/report in Stage 2, run `assert-drained`.
   - If it exits non-zero, do not stop; continue to Stage 3.

If Copilot is already reviewing when Stage 2 starts, do not re-request reviewer;
continue waiting with `run-cycle`.

### Stage 3 (`address_comments`)

User intent: comments already exist and must be processed now.

Actions:

1. Ensure fresh cycle artifacts are available:
   - If state is already `awaiting_address` or `awaiting_triage`, use existing `cycle.json`.
   - Otherwise run `run-cycle` with `--initial-sleep-seconds 0` to capture existing comments immediately.
2. Build normalized worker artifacts in shared context:
   - run `build_review_batch.py` to create `review-batch.json` and `review-batch.md`
3. Run Stage 3 worker actions inside this skill:
   - process all threads from `review-batch.json`
   - account for every Copilot comment in those threads
   - resolve each actionable thread in GitHub
   - reply on each non-actionable thread with rationale
   - do not leave any thread/comment unreviewed or unaddressed
   - push exactly once for the batch
   - do not request Copilot review while processing individual threads
   - update `cycle.json.addressing` and write `address-summary.md`
4. Validate `cycle.json.addressing` before finalizing:
   - `status=ready_for_finalize`
   - `pushed_once=true`
   - `review_id` and `cycle` match active state
   - `threads.addressed + threads.rejected_with_rationale` equals total thread count
   - `threads.needs_clarification=0`
   - `thread_responses` has exactly one entry per thread
   - for each `thread_responses` entry:
     - `classification=actionable` requires `resolved=true`
     - `classification=non-actionable` requires `rationale_replied=true`
   - `comments.addressed_or_rationalized` equals total comment count
   - `comments.needs_clarification=0`
   - `comment_statuses` has exactly one entry per comment with:
     - `status` in `{action, no_action}`
     - `cycle` equal to the active cycle
     - chronological sort by `created_at`
5. Run `finalize-cycle` only when validation passes (re-requests Copilot unless explicitly skipped for recovery).
   - run this once per cycle, after the full thread batch is complete
   - never run it immediately after addressing a single thread
   - never call reviewer add/remove directly during Stage 3; `finalize-cycle` is the only allowed reviewer request path
6. Return to Stage 2.

## Command Templates

### Initialize State

```bash
python "<path-to-skill>/scripts/run_autopilot_loop.py" \
  --repo "." \
  --pr "<PR_NUMBER_OR_URL>" \
  init \
  --initial-sleep-seconds 300 \
  --poll-interval-seconds 45 \
  --cycle-max-wait-seconds 2400
```

Use `--force` with `init` only when intentionally resetting prior state.
If reusing an existing PR branch, do not run `--force` unless the current
state is stale or corrupted.

### Monitor One Cycle (normal wait)

```bash
python "<path-to-skill>/scripts/run_autopilot_loop.py" \
  --repo "." \
  --pr "<PR_NUMBER_OR_URL>" \
  run-cycle \
  --initial-sleep-seconds 300 \
  --poll-interval-seconds 45 \
  --cycle-max-wait-seconds 2400
```

### Capture Existing Comments Immediately (Stage 3 bootstrap)

```bash
python "<path-to-skill>/scripts/run_autopilot_loop.py" \
  --repo "." \
  --pr "<PR_NUMBER_OR_URL>" \
  run-cycle \
  --initial-sleep-seconds 0 \
  --poll-interval-seconds 45 \
  --cycle-max-wait-seconds 2400
```

### Build Stage 3 Worker Batch Artifacts

```bash
python "<path-to-skill>/scripts/build_review_batch.py" \
  --cycle ".context/gh-autopilot/cycle.json" \
  --output-dir ".context/gh-autopilot"
```

### Finalize Addressed Cycle

```bash
python "<path-to-skill>/scripts/run_autopilot_loop.py" \
  --repo "." \
  --pr "<PR_NUMBER_OR_URL>" \
  finalize-cycle
```

This command validates `cycle.json.addressing` coverage first, then:

1. Moves `pending_review_id` into `last_processed_review_id`.
2. Increments `cycle`.
3. Re-requests Copilot via remove/add reviewer sequence.
4. Writes/updates `comment-status-history.json` with per-comment status (`action`/`no_action`) and cycle.

Use `--skip-reviewer-request` only for manual recovery paths.

### Print Current State

```bash
python "<path-to-skill>/scripts/run_autopilot_loop.py" \
  --repo "." \
  --pr "<PR_NUMBER_OR_URL>" \
  status
```

### Assert No Pending Address-Required Cycle

```bash
python "<path-to-skill>/scripts/run_autopilot_loop.py" \
  --repo "." \
  --pr "<PR_NUMBER_OR_URL>" \
  assert-drained
```

Use this as the final gate before reporting completion/timeout handling results.
If state is `awaiting_address` or `awaiting_triage`, this command fails and
the loop must continue through Stage 3.

### Artifacts and Exit Codes from `run-cycle`

Outputs (default `.context/gh-autopilot/`):

- `monitor.json`
- `cycle.json`
- `review-batch.json` (generated by Stage 3 worker setup)
- `review-batch.md` (generated by Stage 3 worker setup)
- `address-summary.md` (generated by Stage 3 worker)
- `comment-status-history.json` (updated on successful finalize)
- `context.md` (updated)

Status meanings:

- `completed_no_comments`: terminal success
- `timeout`: terminal timeout for current run
- `awaiting_address`: actionable Copilot comments captured
- `awaiting_triage`: review exists but needs manual interpretation

Exit codes:

- `0`: terminal success or already-terminal state
- `3`: timeout
- `10`: comments/triage action required
- `11`: `assert-drained` detected unaddressed pending cycle

## Loop Contract

After entering via the user-selected stage, keep routing until terminal.
Do not stop after a single cycle unless blocked by auth/state errors.

```text
current_stage = user_selected_stage
while true:
  if current_stage == 1:
    run Stage 1
    current_stage = 2
    continue

  if current_stage == 2:
    run Stage 2
    if status in {completed_no_comments, timeout}:
      if assert-drained != 0:
        current_stage = 3
        continue
      stop
    current_stage = 3
    continue

  if current_stage == 3:
    run Stage 3 worker handoff
    if cycle.addressing.status != ready_for_finalize:
      stop and request clarification
    if cycle.addressing does not cover all review comments:
      stop and request clarification
    current_stage = 2
    continue
```

## Recovery Scenarios

Handle common failure modes explicitly:

1. Auth failure:
   - Run `gh auth status`.
   - If unauthenticated, run `gh auth login` and retry.
2. State/PR mismatch:
   - If state PR differs from intended PR, re-run `init` with correct `--pr`.
   - Use `--force` only when intentionally discarding prior loop state.
3. Closed/merged PR mid-loop:
   - Stop loop.
   - Open or select a new active PR.
   - Re-initialize state for that PR.
4. Existing open PR before start:
   - Skip `gh-pr-creation`.
   - Initialize directly against that PR.
5. Copilot already reviewing when loop starts (Stage 2):
   - Skip re-request.
   - Run `run-cycle` and allow the per-cycle wait window to finish.
   - Continue normal addressing flow when cycle comments arrive.
6. Copilot comments already present when loop starts (Stage 3):
   - Run immediate capture (`--initial-sleep-seconds 0`) only if cycle artifacts are missing/stale.
   - Build `review-batch.json` in `.context/gh-autopilot/`.
   - Address comments directly in Stage 3 of this skill.
   - Finalize only when `cycle.json.addressing` reports ready and full comment coverage.
   - Resume Stage 2.
7. Agent interruption or handoff:
   - Resume from `.context/gh-autopilot/context.md`.
   - Continue using `context.md` as the source of next actions and state snapshot.

## Safety Rules

- Never process a cycle while state is already `awaiting_address`.
- Never finalize a cycle without confirming comments were fully addressed.
- Never finalize a cycle if any review thread lacks a resolve/rationale response.
- Never claim terminal completion unless `assert-drained` exits `0`.
- Keep one push per cycle.
- Do not delete `.context/gh-autopilot/` artifacts mid-loop.
- Keep `context.md` in sync by using engine commands (`init`, `run-cycle`, `finalize-cycle`) rather than manual edits.

## Optional Utility Scripts

The following scripts remain available for ad-hoc diagnostics:

- `scripts/monitor_copilot_review.py`
- `scripts/export_copilot_feedback.py`

Prefer `run_autopilot_loop.py` for normal loop operation.
