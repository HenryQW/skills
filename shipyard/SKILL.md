---
name: shipyard
description: Execute a dependency-aware GitHub parent issue by running unblocked child issues through issue-workbench, choosing child PR mode on the default branch and integration worktree mode on any other branch. Use when a parent issue from issue-blueprint should be advanced across child issues, parallel worktrees, checks, reviews, and the final_check child.
---

# Shipyard

## Overview

Advance one dependency-aware parent issue without copying the child skills' work.
This skill decides what runs next; `$issue-workbench`, `$ci-repairbay`, and `$review-repairbay` do the implementation, CI, and review-comment work.
Mode selection is automatic:

- If the current branch is the repository default branch, run child PR mode. Do not merge child PRs itself.
- If the current branch is not the default branch, treat the current branch as the shipyard integration branch. Run child worktrees and auto-merge returned child branches into it.

## Inputs

- `parent_issue` is required: the GitHub issue number or URL for the parent issue.

Infer everything else:

- Repository: current directory's GitHub remote.
- Base branch: repository default branch.
- Mode: current branch equals default branch means child PR mode; any other branch means integration mode.
- Behavior: inspect and report ready work unless the user explicitly asks to execute/run the parent issue.

## Workflow

1. Read repository and parent issue state.
   - Confirm `gh auth status`.
   - Resolve the target repo from the current directory.
   - Resolve the repository default branch and current branch.
   - Stop if the current checkout is detached.
   - Read the parent issue body and child issues with `gh issue view`.
   - Extract child issue numbers, `Blocked by`, `Blocks`, `Parallelism`, and any `final_check` child.
   - Stop if the parent issue does not describe a dependency graph clearly enough to choose runnable work.

2. Classify child issues.
   - Runnable: every blocker is closed and merged into the base branch, or in integration mode already merged into the current shipyard branch during this run.
   - Blocked: at least one blocker is open, unmerged, or missing.
   - Pending PR: the child has an open PR that is not merged.
   - Done: the child issue is closed and its PR is merged. In integration mode, complete for the current run means the child branch is merged into the shipyard branch.
   - Final check: the child whose body or parent issue role says `final_check`.

3. Respect execution boundaries.
   - Do not run blocked children.
   - In child PR mode, do not create stacked PRs; wait for blockers to merge into the base branch.
   - In child PR mode, never merge child PRs itself.
   - In integration mode, use the current branch as the shipyard integration branch and merge child branches into it.
   - Do not run the `final_check` child until every non-final child is done.
   - In child PR mode, run one child at a time.
   - In integration mode, run all dependency-ready non-final children the graph allows; parallel children may run in separate worktrees.

4. Execute the next runnable child in normal PR mode.
   - Use this path only when the current branch is the default branch.
   - Ensure the worktree is clean, then switch to and fast-forward the base branch.
   - Run `$issue-workbench <child_issue>` from the base branch.
   - Treat the returned PR URL as the child implementation PR.
   - Record the child issue, branch, and PR URL in `.context/progress.md`; do not commit `.context/`.

5. Execute children in integration mode.
   - Use this path only when the current branch is not the default branch.
   - Ensure the caller worktree is clean.
   - Treat the caller worktree and current branch as the shipyard worktree and integration branch.
   - For each runnable non-final child allowed by the dependency graph, choose a deterministic sibling worktree path such as `../<repo>-shipyard-<parent_issue>-child-<child_issue>`.
   - Stop if any child worktree path already exists.
   - Launch `$issue-workbench <child_issue>` with `worktree_path=<path>`, `handoff_mode=integration_branch`, and `integration_branch=<current_branch>`.
   - Each child issue-workbench returns `branch=<child_branch>` and `worktree=<child_worktree>` instead of a PR URL.
   - In the shipyard worktree, merge each returned child branch into the current branch.
   - If a merge conflicts, stop and report the child issue, child branch, child worktree, and conflicted files.
   - After each merge, run the smallest relevant validation command discoverable in the repo.
   - Do not delete child worktrees automatically.

6. Finish integration mode.
   - After every non-final child is merged into the current branch, stop if the parent issue has no `final_check` child.
   - Run `final_check` through `$issue-workbench` with a new child worktree, `handoff_mode=integration_branch`, and `integration_branch=<current_branch>`.
   - Merge the returned `final_check` branch into the shipyard branch.
   - Run `$review-checkpoint` on the shipyard branch as the final review gate.
   - Run `pr-launchpad` from the shipyard branch to open one PR into the base branch.
   - Treat that returned PR URL as the shipyard implementation PR.

7. Route PR health by signal type.
   - Pass the PR URL returned by `$issue-workbench` to cleanup skills.
   - In integration mode, pass the final shipyard PR URL to cleanup skills.
   - Failing GitHub Actions checks: use `$ci-repairbay` on that PR URL.
   - Unresolved review threads, requested changes, or inline comments: use `$review-repairbay` on that PR URL for all unresolved actionable threads.
   - External failed checks without GitHub Actions logs: report the check URL and stop.
   - Pending checks or pending reviews: stop and report the pending state unless the user asked to wait.
   - Clean PR with no unresolved review threads and passing checks: report that it is ready for merge.

8. Loop conservatively.
   - Re-read parent issue, child issue, and PR state before choosing the next child.
   - Continue only while a child is runnable and the previous child is not pending review, CI, or merge.
   - In integration mode, continue only until the final shipyard PR is created and routed once.
   - Stop when no runnable work remains.

## State Rules

- The GitHub parent issue is the durable source of truth.
- Child issue bodies define dependencies; PR state defines implementation progress.
- `.context/progress.md` is scratch state for the current agent only.
- A child issue is not done because a PR exists; it is done only when the PR is merged or the issue is otherwise explicitly closed.
- In child PR mode, a blocker is not cleared because its PR passes; it is cleared only when merged into the base branch.
- In integration mode, a blocker can clear for the current run after the blocker child branch is merged into the current shipyard branch.
- In integration mode, a child is complete for the current shipyard run only after its branch is merged into the shipyard branch. The durable completion signal is still the final shipyard PR merging or the issue being explicitly closed.

## Health Router

Use this order after every sequential `$issue-workbench` PR or final integration PR:

1. Read checks with `gh pr checks`.
2. If a failing check is a GitHub Actions run, invoke `$ci-repairbay`.
3. If review state shows requested changes, unresolved threads, or inline comments, invoke `$review-repairbay` on the PR URL.
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
- Child issue executed, or child issues merged in integration mode.
- PR URL, using the final shipyard PR in integration mode.
- Integration branch and child worktree paths when integration mode ran.
- CI/review routing performed.
- Verification commands actually run.
- Current stop reason and next runnable issue, if any.
