---
name: review-checkpoint
description: Run Greptile review loops on the current branch and fix actionable findings, with subagent adversarial review fallback when Greptile is unavailable. Use when Codex is asked to run Greptile, run a Greptile review loop, apply Greptile feedback, or use Greptile as a final review gate for local branch changes.
---

# review-checkpoint

## Goal

Use Greptile first as a branch-diff review gate. If Greptile is unavailable, use subagent adversarial review. Fix only deterministic, in-scope findings.

## Inputs

- `max_iterations` is optional and defaults to `5`.
- `poll_interval_seconds` is optional and defaults to `300`.

## Rules

- Do not start a new review just to poll. Poll the same review ID.
- A finding is actionable only when it is in the branch diff, deterministic, in scope, and fixable without a product decision.
- Ignore broad cleanup, optional improvements, unclear requests, and anything outside the branch diff.
- If Greptile is unavailable, use one subagent adversarial branch-diff review as the review gate instead of stopping.
- Keep `.context/progress.md` local and uncommitted if used for review IDs.
- Each fix iteration must resolve or reduce the actionable finding set.
- Stop if the same finding repeats after a targeted fix or if the iteration budget is spent.

## Before review

Run:

```bash
git status --short
```

Start Greptile only from a clean working tree. `.context/progress.md` may remain uncommitted.

If the `greptile` command is missing, cannot start or show a review because of auth/service/plan availability, or returns no review ID, do not install or repair Greptile unless the user asked. Record the error and run the fallback.

## Fallback

When Greptile is unavailable, delegate one adversarial review to a subagent:

- Use a prompt that includes `working_directory=<absolute path>` as the first field.
- Collect and pass the exact review payload yourself: `git branch --show-current`, review base if known, changed files, `git diff --stat <base>...HEAD`, `git diff <base>...HEAD`, and validation commands/results.
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
diff_stat=<captured stat>
diff=<captured diff or path to diff artifact>
verification=<commands and results>

Review only this diff. Do not inspect another worktree. Do not edit files, commit, push, or review broad cleanup. Report deterministic in-scope findings with file/line evidence, or PASS.
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

If still running, wait `poll_interval_seconds` seconds and run the same `show` command again until complete.

If `show` fails because Greptile is unavailable, use the fallback.

Classify findings from the full `show` output.

If no actionable findings remain, stop.

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

Report review IDs or fallback reviews, checks run, final status, and unresolved actionable findings if any.
