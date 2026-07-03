---
name: shipyard
description: Execute dependency-aware GitHub tracker issue graphs by running unblocked child issues through issue-to-code, then routing each created PR through CI and review-comment cleanup. Use when a tracker issue from grill-to-issues or review-to-issues should be advanced across child issues, PRs, checks, reviews, and the final_check child.
---

# Shipyard

## Overview

Advance one dependency-aware implementation tracker without copying the child skills' work.
This skill decides what runs next; `$issue-to-code`, `$gh-fix-ci`, and `$gh-address-comments` do the implementation, CI, and review-comment work.

## Inputs

- `tracker_issue` is required: a GitHub issue number or URL for the implementation tracker.
- `repo` is optional when the current directory resolves to the target GitHub repository.
- `base_branch` is optional and defaults to the repository default branch.
- `mode` is optional and defaults to `plan` unless the user explicitly asks to execute or run issues:
  - `plan`: inspect graph and report ready work only.
  - `run`: execute ready child issues until blocked.

## Workflow

1. Read repository and tracker state.
   - Confirm `gh auth status`.
   - Resolve the target repo and tracker issue.
   - Read the tracker body and child issues with `gh issue view`.
   - Extract child issue numbers, `Blocked by`, `Blocks`, `Parallelism`, and any `final_check` child.
   - Stop if the tracker does not describe a dependency graph clearly enough to choose runnable work.

2. Classify child issues.
   - Runnable: every blocker is closed and merged into `base_branch`.
   - Blocked: at least one blocker is open, unmerged, or missing.
   - Pending PR: the child has an open PR that is not merged.
   - Done: the child issue is closed and its PR is merged.
   - Final check: the child whose body or tracker role says `final_check`.

3. Respect execution boundaries.
   - Do not run blocked children.
   - Do not create stacked PRs by default; wait for blockers to merge into `base_branch`.
   - Do not run the `final_check` child until every non-final child is done.
   - If multiple children are runnable, run one at a time unless the user explicitly asks for parallel agents.

4. Execute the next runnable child.
   - Ensure the worktree is clean, then switch to and fast-forward `base_branch`.
   - Run `$issue-to-code <child_issue>` from `base_branch` with the resolved `base_branch`.
   - Treat the returned PR URL as the child implementation PR.
   - Record the child issue, branch, and PR URL in `.context/progress.md`; do not commit `.context/`.

5. Route PR health by signal type.
   - Failing GitHub Actions checks: use `$gh-fix-ci` on that PR.
   - Unresolved review threads, requested changes, or inline comments: use `$gh-address-comments` on that PR for all unresolved actionable threads.
   - External failed checks without GitHub Actions logs: report the check URL and stop.
   - Pending checks or pending reviews: stop and report the pending state unless the user asked to wait.
   - Clean PR with no unresolved review threads and passing checks: report that it is ready for merge.

6. Loop conservatively.
   - Re-read tracker, child issue, and PR state before choosing the next child.
   - Continue only while a child is runnable and the previous child is not pending review, CI, or merge.
   - Stop when no runnable work remains.

## State Rules

- The GitHub tracker issue is the durable source of truth.
- Child issue bodies define dependencies; PR state defines implementation progress.
- `.context/progress.md` is scratch state for the current agent only.
- A child issue is not done because a PR exists; it is done only when the PR is merged or the issue is otherwise explicitly closed.
- A blocker is not cleared because its PR passes; it is cleared only when merged into `base_branch`.

## Health Router

Use this order after every `$issue-to-code` PR:

1. Read checks with `gh pr checks`.
2. If a failing check is a GitHub Actions run, invoke `$gh-fix-ci`.
3. If review state shows requested changes, unresolved threads, or inline comments, invoke `$gh-address-comments` on the PR.
4. In `run` mode, treat the user's execution request as approval to let `$gh-address-comments` fix, reply, resolve, and re-fetch actionable review threads unless the user restricted GitHub writes.
5. In `plan` mode, report review state without writes.
6. If only resolved, outdated, informational, approval, or top-level summary comments exist, do not run a cleanup skill.
7. If the PR is blocked by human approval, merge permissions, or an external provider, stop and report the blocker.

## Output

For `plan` mode, return:

- Tracker issue URL.
- Child issue table: issue, state, blockers, PR, next action.
- Runnable set.
- Stop reason.

For `run` mode, return:

- Tracker issue URL.
- Child issue executed.
- PR URL.
- CI/review routing performed.
- Verification commands actually run.
- Current stop reason and next runnable issue, if any.
