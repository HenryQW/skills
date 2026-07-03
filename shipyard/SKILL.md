---
name: shipyard
description: Execute a dependency-aware GitHub parent issue by running unblocked child issues through issue-workbench, then routing each created PR through CI and review-comment cleanup. Use when a parent issue from issue-blueprint should be advanced across child issues, PRs, checks, reviews, and the final_check child.
---

# Shipyard

## Overview

Advance one dependency-aware parent issue without copying the child skills' work.
This skill decides what runs next; `$issue-workbench`, `$ci-repairbay`, and `$review-repairbay` do the implementation, CI, and review-comment work.

## Inputs

- `parent_issue` is required: the GitHub issue number or URL for the parent issue.

Infer everything else:

- Repository: current directory's GitHub remote.
- Base branch: repository default branch.
- Behavior: inspect and report ready work unless the user explicitly asks to execute/run the parent issue.

## Workflow

1. Read repository and parent issue state.
   - Confirm `gh auth status`.
   - Resolve the target repo from the current directory.
   - Read the parent issue body and child issues with `gh issue view`.
   - Extract child issue numbers, `Blocked by`, `Blocks`, `Parallelism`, and any `final_check` child.
   - Stop if the parent issue does not describe a dependency graph clearly enough to choose runnable work.

2. Classify child issues.
   - Runnable: every blocker is closed and merged into the base branch.
   - Blocked: at least one blocker is open, unmerged, or missing.
   - Pending PR: the child has an open PR that is not merged.
   - Done: the child issue is closed and its PR is merged.
   - Final check: the child whose body or parent issue role says `final_check`.

3. Respect execution boundaries.
   - Do not run blocked children.
   - Do not create stacked PRs by default; wait for blockers to merge into the base branch.
   - Do not run the `final_check` child until every non-final child is done.
   - If multiple children are runnable, run one at a time unless the user explicitly asks for parallel agents.

4. Execute the next runnable child.
   - Ensure the worktree is clean, then switch to and fast-forward the base branch.
   - Run `$issue-workbench <child_issue>` from the base branch.
   - Treat the returned PR URL as the child implementation PR.
   - Record the child issue, branch, and PR URL in `.context/progress.md`; do not commit `.context/`.

5. Route PR health by signal type.
   - Failing GitHub Actions checks: use `$ci-repairbay` on that PR.
   - Unresolved review threads, requested changes, or inline comments: use `$review-repairbay` on that PR for all unresolved actionable threads.
   - External failed checks without GitHub Actions logs: report the check URL and stop.
   - Pending checks or pending reviews: stop and report the pending state unless the user asked to wait.
   - Clean PR with no unresolved review threads and passing checks: report that it is ready for merge.

6. Loop conservatively.
   - Re-read parent issue, child issue, and PR state before choosing the next child.
   - Continue only while a child is runnable and the previous child is not pending review, CI, or merge.
   - Stop when no runnable work remains.

## State Rules

- The GitHub parent issue is the durable source of truth.
- Child issue bodies define dependencies; PR state defines implementation progress.
- `.context/progress.md` is scratch state for the current agent only.
- A child issue is not done because a PR exists; it is done only when the PR is merged or the issue is otherwise explicitly closed.
- A blocker is not cleared because its PR passes; it is cleared only when merged into the base branch.

## Health Router

Use this order after every `$issue-workbench` PR:

1. Read checks with `gh pr checks`.
2. If a failing check is a GitHub Actions run, invoke `$ci-repairbay`.
3. If review state shows requested changes, unresolved threads, or inline comments, invoke `$review-repairbay` on the PR.
4. When the user asked to execute/run the parent issue, treat that as approval to let `$review-repairbay` fix, reply, resolve, and re-fetch actionable review threads unless the user restricted GitHub writes.
5. When the user asked only to inspect or plan, report review state without writes.
6. If only resolved, outdated, informational, approval, or top-level summary comments exist, do not run a cleanup skill.
7. If the PR is blocked by human approval, merge permissions, or an external provider, stop and report the blocker.

## Output

When inspecting only, return:

- Parent issue URL.
- Child issue table: issue, state, blockers, PR, next action.
- Runnable set.
- Stop reason.

When executing, return:

- Parent issue URL.
- Child issue executed.
- PR URL.
- CI/review routing performed.
- Verification commands actually run.
- Current stop reason and next runnable issue, if any.
