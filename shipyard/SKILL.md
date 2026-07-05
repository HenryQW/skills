---
name: shipyard
description: Orchestrate a dependency-aware GitHub parent issue from a parent-derived non-default integration branch by running unblocked child issues through issue-workbench, merging child worktrees into the current branch, and opening one final PR. Use when a parent issue from issue-blueprint should be advanced across child issues, parallel worktrees, checks, reviews, and the final_check child; stop when the current branch is the repository default branch.
---

# Shipyard

## Overview

Advance one dependency-aware parent issue without copying the child skills' work.
Shipyard is orchestration only: inspect the graph, launch child worktrees, merge returned child branches, run integration checks, classify final review findings, and create the final PR.
`$issue-workbench`, `$ci-repairbay`, `$review-repairbay`, `$review-checkpoint`, and `$pr-launchpad` own implementation, actionable review fixes, CI, review comments, review gates, and PR creation.

Shipyard has one execution mode:

- `$shipyard #123` or `shipyard #123` means execute parent issue `#123`.
- The current branch must be the parent-derived shipyard integration branch.
- If the current branch is the repository default branch, stop before creating child worktrees, branches, commits, merges, or PRs.
- Inspect-only behavior is allowed only when the user explicitly asks to inspect, plan, dry-run, or report without executing.

## Inputs

- `parent_issue` is required: the GitHub issue number or URL for the parent issue.
- If the user passes `--integration-worktree <absolute_path>`, `cd` there before inspecting. The path must be absolute.

Infer everything else:

- Repository: current directory's GitHub remote.
- Base branch: repository default branch.
- Integration branch: current non-default branch, which must match the parent-derived name from `python3 <issue_workbench_dir>/scripts/branch_name.py integration <parent_issue>`.
- Behavior: execute unless the user explicitly asks for inspect-only output.

## Bundled Resources

- `scripts/inspect_parent_issue.py`: resolves branch policy, parent issue, child issue dependencies, `final_check`, local merged children, and runnable children.
- `<issue_workbench_dir>/scripts/integration_child.py`: starts child worktrees and merges returned child branches; resolve `<issue_workbench_dir>` from the loaded `issue-workbench` skill path.

## Runnable CLI Flow

Use these commands as the deterministic spine. Shipyard owns orchestration, integration checks, and PR creation; `$issue-workbench` owns child implementation and actionable review fixes.

```bash
gh auth status
python3 <shipyard_dir>/scripts/inspect_parent_issue.py <parent_issue> --json
python3 <issue_workbench_dir>/scripts/branch_name.py integration <parent_issue>
# stop here if mode is default_branch_blocked
python3 <issue_workbench_dir>/scripts/integration_child.py start <child_issue> --worktree-path <absolute_child_worktree> --integration-branch <integration_branch>
# run $issue-workbench in the child worktree
python3 <issue_workbench_dir>/scripts/integration_child.py merge <child_branch> --integration-branch <integration_branch>
python3 <shipyard_dir>/scripts/inspect_parent_issue.py <parent_issue> --json
```

After all non-final children are merged, run `final_check` the same way. For a verification-only `final_check`, no empty commit is required; empty `diff_stat` plus `commit` equal to the shipyard branch HEAD is the expected no-op result.

## Workflow

1. Inspect repository and issue graph.
   - Confirm `gh auth status`.
   - If the user passed `--integration-worktree`, stop unless it is absolute, then `cd` there before inspecting.
   - Run `python3 <skill_dir>/scripts/inspect_parent_issue.py <parent_issue> --json`.
   - Stop if the script cannot resolve a parent issue, current branch, dependency graph, or runnable state.
   - If `mode` is `default_branch_blocked`, report the default branch, current branch, and instruction to create or switch to a non-default integration branch.
   - Run `python3 <issue_workbench_dir>/scripts/branch_name.py integration <parent_issue>`.
   - Stop if the current branch differs from the expected integration branch. Do not rename automatically; report `git branch -m <expected_branch>` and, if the branch was pushed, the needed push/upstream commands.
   - If child issues name explicit files and acceptance criteria, read only matching active handoff/index sections and issue-linked docs. Use broad repository or vault searches only when scoped reads are insufficient.

2. Respect execution boundaries.
   - Do not run blocked children.
   - Use the current branch as the shipyard integration branch and merge child branches into it.
   - Do not apply patches for child issue code from the shipyard worktree or parent agent. Spawn or reuse `$issue-workbench` in that child worktree.
   - Shipyard may fix only integration-only issues: merge conflicts, PR body, progress scratch, and final assembly mistakes.
   - Do not run the `final_check` child until every non-final child is done.
   - Run only the currently dependency-ready non-final children as one wave; parallel children may run in separate worktrees.
   - After each integration wave is merged, re-inspect the graph before creating worktrees for newly unblocked children.

3. Execute one integration wave.
   - Ensure the caller worktree is clean.
   - Treat the caller worktree and current branch as the shipyard worktree and integration branch.
   - Let Shipyard own child worktree creation; do not manually create scratch files or child branches outside this flow.
   - Use the latest inspection output as the wave source.
   - The wave includes only non-final children whose current status is `runnable`; skip `blocked`, `blocked-missing`, `blocked-final-check`, `pending-pr`, `done`, and `done-local`.
   - Do not create child worktrees for blocked children in anticipation of unblocking.
   - For each child in the current wave, choose a deterministic sibling worktree path such as `../<repo>-shipyard-<parent_issue>-child-<child_issue>`.
   - Stop if any child worktree path already exists.
   - Launch child workers with this template:

```text
Use $issue-workbench <child_issue>
working_directory=<absolute_child_worktree>
worktree_path=<path>
handoff_mode=integration_branch
integration_branch=<current_branch>
Do not commit .context/.
Return only the JSON object from integration_child.py finish.
```

   - Each child issue-workbench returns one JSON object only after its latest review gate has no actionable findings.
   - Require fields: `branch`, `worktree`, `base`, `commit`, `diff_stat`, `verification`, `review`, `checks`, and `known_skips`; allow optional `needs_child_fix`.
   - Record only `issue`, `worktree`, `branch`, `base`, `commit`, and `status` in `.context/progress.md`; do not commit `.context/`.
   - Stop if any required field is missing, `verification` does not start with `pass:` or `skip:`, `review` is not `PASS` and no `needs_child_fix` is present, or `git rev-parse <branch>` does not match `commit`.
   - If `needs_child_fix` is present, mark that child as `needs_fix`, stop Shipyard edits, and rerun or reuse `$issue-workbench` for that issue in its recorded child worktree.
   - Spot-check returned `diff_stat`. Inspect the full child diff before merge only when the diff touches high-risk paths or is not obviously tiny.
   - In the shipyard worktree, merge only returned child branches into the current branch, preferably with `python3 <issue_workbench_dir>/scripts/integration_child.py merge <child_branch> --integration-branch <current_branch>`.
   - If a merge conflicts, stop and report the child issue, child branch, child worktree, and conflicted files.
   - After each merge, run the smallest relevant validation command discoverable in the repo.
   - Do not delete child worktrees automatically.
   - Once multiple worktrees exist, use absolute paths in all `apply_patch` edits and shell commands that create or mutate files.

   Keep this compact state object in `.context/progress.md` after every child return or merge:

```json
{"tracker":"#<parent>","mode":"integration","children":[{"issue":"#<n>","worktree":"/abs/path","branch":"issue-<n>","base":"<integration_branch>","commit":"<sha>","status":"returned|merged|needs_fix"}],"checks":["<command>"],"current_step":"<next action>"}
```

4. Finish integration.
   - After each wave is merged, rerun `python3 <skill_dir>/scripts/inspect_parent_issue.py <parent_issue> --json`.
   - If newly runnable non-final children exist, repeat Step 3 before `final_check`.
   - If non-final children remain blocked, pending, or missing, stop and report the blockers instead of running `final_check`.
   - After every non-final child is merged into the current branch or otherwise done, stop if the parent issue has no `final_check` child.
   - Run `final_check` through `$issue-workbench` with a new child worktree, `handoff_mode=integration_branch`, and `integration_branch=<current_branch>`.
   - If `final_check` is verification-only, instruct the child not to create an empty commit; it should run checks and return the no-op completion signal.
   - If `final_check` discovers code defects, it must fix only final-check-owned docs/tests in its child branch or return `needs_child_fix:"#<issue>"`.
   - Apply the same returned-field recording, missing-field stop, verification-prefix stop, commit-match check, `needs_child_fix` routing, and `diff_stat` spot-check before merging `final_check`.
   - If `final_check` returns an empty `diff_stat` and its returned `commit` already equals the shipyard branch HEAD, record `final_check` as no-op complete and skip merge.
   - Otherwise merge the returned `final_check` branch into the shipyard branch.
   - Run `$review-checkpoint` on the shipyard branch as the final review gate.
   - Classify each final review finding as `child:<issue>`, `final_check`, `integration`, `stale`, `non_actionable`, or `tooling_unavailable`.
   - For `child:<issue>`, stop Shipyard edits, reuse that child's recorded worktree with `$issue-workbench`, merge the child branch again, then rerun the relevant integration checks and final review classification before PR creation.
   - For `final_check`, reuse the recorded `final_check` worktree with `$issue-workbench`, merge it again when it returns a branch, then rerun the relevant integration checks and final review classification before PR creation.
   - Fix only `integration` findings in the shipyard worktree.
   - For `stale`, `non_actionable`, or `tooling_unavailable` findings, record the classification and stop the fix loop for that finding.
   - If Greptile fails because of provider/tooling availability and review-checkpoint substitutes adversarial subagent review, stop retrying Greptile. Record the `tooling_unavailable` classification, error summary, reviewer identity if available, final actionable-finding result, and PR-body testing/review note in `.context/progress.md`.
   - Run `$pr-launchpad` from the shipyard branch to open one PR into the base branch, with close keywords for every child issue, including `final_check`. If the final review gate used a Greptile-unavailable substitution, include the prepared testing/review note in the PR body.
   - Treat that returned PR URL as the shipyard implementation PR.

5. Route PR health.
   - Read checks with `gh pr checks`.
   - If a failing check is a GitHub Actions run, invoke `$ci-repairbay`.
   - If review state shows requested changes, unresolved threads, or inline comments, invoke `$review-repairbay` on the PR URL.
   - When the user asked to execute Shipyard, treat that as approval to let `$review-repairbay` fix, reply, resolve, and re-fetch actionable review threads unless the user restricted GitHub writes.
   - When the user asked only to inspect or plan, report review state without writes.
   - If only resolved, outdated, informational, approval, or top-level summary comments exist, do not run a cleanup skill.
   - If the PR is blocked by human approval, merge permissions, or an external provider, stop and report the blocker.

6. Loop conservatively.
   - Re-read parent issue, child issue, and PR state before choosing the next wave.
   - Continue only while a child is runnable and the previous wave is not pending review, CI, or merge.
   - Continue only until the final shipyard PR is created and routed once.
   - Stop when no runnable work remains.

## Runtime Rules

- Batch one runnable integration wave in parallel; re-inspect before the next wave.
- Stop retrying Greptile after the first provider/tooling failure and run one fallback review.
- Avoid broad final `pytest` when a known readiness hang exists. Run targeted suites and record known skips.

## State Rules

- The GitHub parent issue is the durable source of truth.
- Child issue bodies define dependencies; PR state defines implementation progress.
- `.context/progress.md` is scratch state for the current agent only.
- A child issue is not done because a PR exists; it is done only when the PR is merged, the issue is explicitly closed, or its branch is merged into the current shipyard branch for this run.
- A blocker can clear for the current run after the blocker child branch is merged into the current shipyard branch.
- A child is complete for the current shipyard run only after its branch is merged into the shipyard branch. The durable completion signal is still the final shipyard PR merging or the issue being explicitly closed.
- `done-local` means `issue-<number>` is already merged into the current shipyard branch; do not run that child again even if the GitHub issue is still open.

## Output

When inspecting only, return:

- Parent issue URL.
- Branch policy result: current branch, default branch, and whether execution is blocked.
- Child issue table: issue, state, blockers, PR, next action.
- Runnable set.
- Stop reason.

When executing, return:

- Parent issue URL.
- Child issues merged.
- Final shipyard PR URL.
- Integration branch and child worktree paths.
- Child handoff evidence: issue, worktree, branch, base, commit, status, diff_stat, and verification.
- CI/review routing performed.
- Verification commands actually run.
- Current stop reason and next runnable issue, if any.
