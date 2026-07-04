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

## Bundled Resources

- `scripts/inspect_parent_issue.py`: resolves branch mode, parent issue, child issue dependencies, `final_check`, and runnable children.
- `<issue_workbench_dir>/scripts/integration_child.py`: optional merge helper; resolve `<issue_workbench_dir>` from the loaded `issue-workbench` skill path.

## Workflow

1. Inspect repository and issue graph.
   - Confirm `gh auth status`.
   - Run `python3 <skill_dir>/scripts/inspect_parent_issue.py <parent_issue>`.
   - Stop if the script cannot resolve a parent issue, current branch, dependency graph, or runnable state.
   - If child issues name explicit files and acceptance criteria, read only matching active handoff/index sections and issue-linked docs. Use broad repository or vault searches only when scoped reads are insufficient.

2. Respect execution boundaries.
   - Do not run blocked children.
   - In child PR mode, do not create stacked PRs; wait for blockers to merge into the base branch.
   - In child PR mode, never merge child PRs itself.
   - In integration mode, use the current branch as the shipyard integration branch and merge child branches into it.
   - Do not run the `final_check` child until every non-final child is done.
   - In child PR mode, run one child at a time.
   - In integration mode, run only the currently dependency-ready non-final children as one wave; parallel children may run in separate worktrees.
   - After each integration wave is merged, re-inspect the graph before creating worktrees for newly unblocked children.

3. Execute the next runnable child in normal PR mode.
   - Use this path only when the current branch is the default branch.
   - Ensure the worktree is clean, then switch to and fast-forward the base branch.
   - Run `$issue-workbench <child_issue>` from the base branch.
   - Treat the returned PR URL as the child implementation PR.
   - Record the child issue, branch, and PR URL in `.context/progress.md`; do not commit `.context/`.

4. Execute one integration wave.
   - Use this path only when the current branch is not the default branch.
   - Ensure the caller worktree is clean.
   - Treat the caller worktree and current branch as the shipyard worktree and integration branch.
   - Use the latest inspection output as the wave source.
   - The wave includes only non-final children whose current status is `runnable`; skip `blocked`, `blocked-missing`, `blocked-final-check`, `pending-pr`, `done`, and `done-local`.
   - Do not create child worktrees for blocked children in anticipation of unblocking.
   - For each child in the current wave, choose a deterministic sibling worktree path such as `../<repo>-shipyard-<parent_issue>-child-<child_issue>`.
   - Stop if any child worktree path already exists.
   - Launch child workers with this template:

```text
Use $issue-workbench <child_issue>
worktree_path=<path>
handoff_mode=integration_branch
integration_branch=<current_branch>
Do not commit .context/.
Return only branch=, worktree=, commit=, diff_stat=, and verification= lines.
```

   - Each child issue-workbench returns `branch=`, `worktree=`, `commit=`, `diff_stat=`, and `verification=` only after its latest review gate has no actionable findings.
   - Record those returned fields in `.context/progress.md`; do not commit `.context/`.
   - Stop if any return field is missing, `verification=` does not start with `pass:` or `skip:`, or `git rev-parse <child_branch>` does not match the returned `commit=`.
   - Spot-check returned `diff_stat`. Inspect the full child diff before merge only when the diff touches high-risk paths or is not obviously tiny.
   - In the shipyard worktree, merge only returned child branches into the current branch, preferably with `python3 <issue_workbench_dir>/scripts/integration_child.py merge <child_branch> --integration-branch <current_branch>`.
   - If a merge conflicts, stop and report the child issue, child branch, child worktree, and conflicted files.
   - After each merge, run the smallest relevant validation command discoverable in the repo.
   - Do not delete child worktrees automatically.

5. Finish integration mode.
   - After each wave is merged, rerun `python3 <skill_dir>/scripts/inspect_parent_issue.py <parent_issue>`.
   - If newly runnable non-final children exist, repeat Step 4 before `final_check`.
   - If non-final children remain blocked, pending, or missing, stop and report the blockers instead of running `final_check`.
   - After every non-final child is merged into the current branch or otherwise done, stop if the parent issue has no `final_check` child.
   - Run `final_check` through `$issue-workbench` with a new child worktree, `handoff_mode=integration_branch`, and `integration_branch=<current_branch>`.
   - Apply the same returned-field recording, missing-field stop, verification-prefix stop, commit-match check, and `diff_stat` spot-check before merging `final_check`.
   - If `final_check` returns an empty `diff_stat` and its returned `commit=` already equals the shipyard branch HEAD, record `final_check` as no-op complete and skip merge.
   - Otherwise merge the returned `final_check` branch into the shipyard branch.
   - Run `$review-checkpoint` on the shipyard branch as the final review gate.
   - If Greptile fails because of provider/tooling availability and review-checkpoint substitutes adversarial subagent review, stop retrying Greptile. Record the substitution, error summary, reviewer identity if available, final actionable-finding result, and PR-body testing/review note in `.context/progress.md`.
   - Run `pr-launchpad` from the shipyard branch to open one PR into the base branch, with close keywords for every child issue, including `final_check`. If the final review gate used a Greptile-unavailable substitution, include the prepared testing/review note in the PR body.
   - Treat that returned PR URL as the shipyard implementation PR.

6. Route PR health using Health Router below.
   - In child PR mode, route the PR URL returned by `$issue-workbench`.
   - In integration mode, route the final shipyard PR URL.

7. Loop conservatively.
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
- In integration mode, `done-local` means `issue-<number>` is already merged into the current shipyard branch; do not run that child again even if the GitHub issue is still open.

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
- Child handoff evidence: issue, branch, commit, diff_stat, and verification.
- CI/review routing performed.
- Verification commands actually run.
- Current stop reason and next runnable issue, if any.
