---
name: review-checkpoint
description: Run Greptile review loops on the current branch and fix actionable findings. Use when Codex is asked to run Greptile, run a Greptile review loop, apply Greptile feedback, or use Greptile as a final review gate for local branch changes.
---

# review-checkpoint

## Goal

Use Greptile as a branch-diff review gate. Fix only deterministic, in-scope findings.

## Inputs

- `max_iterations` is optional and defaults to `5`.
- `poll_interval_seconds` is optional and defaults to `300`.

## Rules

- Do not start a new review just to poll. Poll the same review ID.
- A finding is actionable only when it is in the branch diff, deterministic, in scope, and fixable without a product decision.
- Ignore broad cleanup, optional improvements, unclear requests, and anything outside the branch diff.
- Keep `.context/progress.md` local and uncommitted if used for review IDs.
- Each fix iteration must resolve or reduce the actionable finding set.
- Stop if the same finding repeats after a targeted fix or if the iteration budget is spent.

## Before review

Run:

```bash
git status --short
```

Start Greptile only from a clean working tree. `.context/progress.md` may remain uncommitted.

## Loop

Repeat up to `max_iterations`:

```bash
greptile review --agent
```

Record the review ID. If none is returned, stop.

```bash
greptile review show <review_id> --agent
```

If still running, wait `poll_interval_seconds` seconds and run the same `show` command again until complete.

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

Start a new Greptile review only after committing fixes. The final gate is the latest completed review with no later commit.

## Output

Report review IDs, checks run, final status, and unresolved actionable findings if any.
