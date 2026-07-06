---
name: review-checkpoint
description: Run Greptile review loops on the current branch and fix actionable findings, with subagent adversarial review fallback when Greptile is unavailable. Use when Codex is asked to run Greptile, run a Greptile review loop, apply Greptile feedback, or use Greptile as a final review gate for local branch changes.
---

# review-checkpoint

## Goal

Use Greptile first as a branch-diff review gate. If Greptile is unavailable, use subagent adversarial review. Fix only deterministic, in-scope findings.

## Inputs

- `max_iterations` is optional and defaults to `5`.
- `review_base` is optional; use the caller-provided base ref when known.
- `wait_mode` is optional and defaults to `defer`; supported values are `defer` and `block`.
- `poll_interval_seconds` is optional and defaults to `300`; in `defer` mode it sets `poll_after_utc`, and in `block` mode it is the sleep duration.

## Rules

- Do not start a new review just to poll. Poll the same review ID.
- A finding is actionable only when it is in the branch diff, deterministic, in scope, and fixable without a product decision.
- Ignore broad cleanup, optional improvements, unclear requests, and anything outside the branch diff.
- If Greptile is unavailable, use one subagent adversarial branch-diff review as the review gate instead of stopping.
- Keep `.context/progress.md` local and uncommitted if used for pending review state.
- Write fallback review payloads and large diffs to `.context/` artifacts, record their paths in `.context/progress.md`, and pass paths instead of pasted content.
- Each fix iteration must resolve or reduce the actionable finding set.
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

On resume, if `.context/progress.md` contains a pending Greptile review, run `git fetch --all --prune`, then compare its branch, local HEAD SHA, upstream SHA, and known base SHA with current `git branch --show-current`, `git rev-parse HEAD`, `git rev-parse @{upstream}`, and `git rev-parse <review_base>`. Poll that review ID only when recorded values match and current UTC is at or after its poll-after time. If the poll-after time has not arrived, return `PENDING_REVIEW`. If any value differs, or if `base_ref` or `base_sha` is unknown, mark the pending review `stale` with the reason and start a new review after resolving the base.

If the `greptile` command is missing, cannot start or show a review because of auth/service/plan availability, or returns no review ID, do not install or repair Greptile unless the user asked. Record the error and run the fallback.

## Fallback

When Greptile is unavailable, delegate one adversarial review to a subagent:

- Use a prompt that includes `working_directory=<absolute path>` as the first field.
- Collect the exact review payload yourself: `git branch --show-current`, review base if known, changed files, `git diff --stat <base>...HEAD`, `git diff <base>...HEAD`, and validation commands/results.
- Save the full diff and payload under `.context/` and record those absolute paths in `.context/progress.md`.
- Ask the subagent to inspect that branch diff only.
- Tell it to report deterministic, in-scope findings with file/line evidence.
- Tell it not to edit files, commit, push, or review broad cleanup.
- Classify its output with the same actionable-finding rules as Greptile.
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

Review only the artifact paths above. Do not inspect another worktree. Do not edit files, commit, push, or review broad cleanup. Report deterministic in-scope findings with file/line evidence, or PASS.
```

Treat the completed subagent review as the current review output. If fixes are committed and Greptile is still unavailable, run another subagent review for the next iteration.

## Loop

Repeat up to `max_iterations`:

```bash
greptile review --agent
```

Record the review ID. If none is returned, use the fallback.

```bash
greptile review show <review_id> --agent
```

If still running and `wait_mode=defer`, write pending state to `.context/progress.md` and return `PENDING_REVIEW` instead of sleeping. Include at least:

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

If still running and `wait_mode=block`, wait the configured `poll_interval_seconds` exactly and run the same `show` command again until complete. Do not poll at a hardcoded 30-second interval unless the caller configured `poll_interval_seconds=30`.

If `show` fails because Greptile is unavailable, use the fallback.

Classify findings from the full `show` output.

If no actionable findings remain, stop.

If a finding repeats after a targeted fix but now asks for the opposite behavior, classify it as `non_actionable: contradictory semantics`, record both review IDs, and stop fixing that finding.

Fix the smallest set of files needed for actionable findings, then inspect and validate:

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

Start a new Greptile review, or fallback subagent review when Greptile is still unavailable, only after committing fixes. The final gate is the latest completed review with no later commit.

## Output

Report review IDs or fallback reviews, checks run, final status, and unresolved actionable findings if any. For deferred reviews, return `PENDING_REVIEW` with the pending review state location.
