---
name: shipyard
description: Orchestrate a dependency-aware parent issue from its deterministic integration branch into one final PR. Use for issue-blueprint parent issues that need child worktrees, merges, final_check, checks, reviews, and PR routing.
---

# Shipyard

## Overview

Advance one dependency-aware parent issue without copying the child skills' work.
Shipyard is orchestration only: inspect the graph, launch child worktrees, merge returned child branches, run integration checks, classify final review findings, and create the final PR.
`$issue-workbench`, `$ci-repairbay`, `$review-repairbay`, `$review-checkpoint`, and `$pr-launchpad` own implementation, actionable review fixes, CI, review comments, review gates, and PR creation.

Shipyard has one execution mode:

- `$shipyard #123` or `shipyard #123` means execute parent issue `#123`.
- Reconcile to the parent-derived shipyard integration branch before creating child worktrees, branches, commits, merges, or PRs.
- Inspect-only behavior is allowed only when the user explicitly asks to inspect, plan, dry-run, or report without executing.

## Inputs

- `parent_issue` is required: the GitHub issue number or URL for the parent issue.
- If the user passes `--integration-worktree <absolute_path>`, `cd` there before inspecting. The path must be absolute.

Infer everything else:

- Repository: current directory's GitHub remote.
- Base branch: repository default branch.
- Integration branch: parent-derived name from `python3 <issue_workbench_dir>/scripts/branch_name.py integration <parent_issue>`.
- Behavior: execute unless the user explicitly asks for inspect-only output.

## Bundled Resources

- `scripts/inspect_parent_issue.py`: resolves branch policy, parent issue, child issue dependencies, `final_check`, local merged children, and runnable children.
- `<issue_workbench_dir>/scripts/integration_child.py`: starts child worktrees and merges returned child branches; resolve `<issue_workbench_dir>` from the loaded `issue-workbench` skill path.

## CLI Spine

Use these commands as the deterministic spine:

```bash
python3 <issue_workbench_dir>/scripts/branch_name.py integration <parent_issue>
gh repo view --json defaultBranchRef --jq .defaultBranchRef.name
# reconcile to that branch, then inspect
python3 <shipyard_dir>/scripts/inspect_parent_issue.py <parent_issue> --json
python3 <issue_workbench_dir>/scripts/integration_child.py start <child_issue> --worktree-path <absolute_child_worktree> --integration-branch <integration_branch>
# run $issue-workbench in the child worktree
python3 <issue_workbench_dir>/scripts/integration_child.py merge <child_branch> --integration-branch <integration_branch>
python3 <shipyard_dir>/scripts/inspect_parent_issue.py <parent_issue> --json
```

After all non-final children are merged, run `final_check` the same way. For a verification-only `final_check`, no empty commit is required; empty `diff_stat` plus `commit` equal to the shipyard branch HEAD is the expected no-op result.

## State Machine

### 1. Preflight

- If `--integration-worktree` is present, require an absolute path and `cd` there.
- Compute the expected branch with `python3 <issue_workbench_dir>/scripts/branch_name.py integration <parent_issue>`.
- Resolve the default branch with `gh repo view --json defaultBranchRef --jq .defaultBranchRef.name`.
- Ensure `git status --porcelain` is empty before changing branches; stop with dirty paths if not.
- Run `git fetch --all --prune`.
- If the current branch differs from the expected branch:
  - If the expected branch exists locally, run `git switch <expected_branch>`.
  - Else if `origin/<expected_branch>` exists, run `git switch --track -c <expected_branch> origin/<expected_branch>`.
  - Else if the current branch is not `<default_branch>` and `git rev-parse --abbrev-ref --symbolic-full-name @{u}` fails, run `git branch -m <expected_branch>`.
  - Else if `origin/<default_branch>` exists, run `git switch -c <expected_branch> origin/<default_branch>`.
  - Else run `git switch -c <expected_branch> <default_branch>`.
- Never rename the default branch.
- Run `python3 <skill_dir>/scripts/inspect_parent_issue.py <parent_issue> --json` after branch reconciliation.
- Stop if the script cannot resolve the parent, current branch, dependency graph, or runnable state.
- Stop on `mode=default_branch_blocked`; report the default branch, current branch, and failed branch-reconciliation command.
- Read only issue-linked docs or named files needed to understand runnable children.

### 2. Run one wave

- Ensure the shipyard worktree is clean.
- Use the current branch as the integration branch.
- Run only current non-final children with status `runnable`; do not pre-create blocked children.
- Choose deterministic sibling worktree paths such as `../<repo>-shipyard-<parent_issue>-child-<child_issue>` and stop if a path already exists.
- Launch children in parallel with this prompt:

```text
Use $issue-workbench <child_issue>
working_directory=<absolute_child_worktree>
worktree_path=<path>
handoff_mode=integration_branch
integration_branch=<current_branch>
review_base=<current_branch>
wait_mode=defer
Do not commit .context/.
Write detailed artifacts to .context/progress.md in the child worktree.
Return only the compact child handoff JSON object.
```

- Require one child handoff JSON object with `branch`, `worktree`, `base`, `commit`, `diff_stat`, `verification`, `review`, `checks`, `known_skips`, and `artifacts.progress_path`; allow `needs_child_fix`.
- Accept only `review:"PASS"`, `review:"PENDING_REVIEW"`, or `review:"FAIL"` with `needs_child_fix`.
- Accept `review:"PENDING_REVIEW"` only with `pending_review` evidence containing `review_id`, `local_head_sha`, `upstream_sha`, `base_ref`, `base_sha`, `poll_after_utc`, and `progress_path`.
- Stop if a required field is missing, `verification` does not start with `pass:` or `skip:`, the review value is not accepted, or `git rev-parse <branch>` differs from `commit`.
- If `needs_child_fix` is present, mark `needs_fix`, stop shipyard edits, and rerun or reuse `$issue-workbench` in that child worktree.
- If `review` is `PENDING_REVIEW`, mark `pending_review`, record the evidence, do not merge the branch, and continue other runnable independent children when available.
- Spot-check `diff_stat`; inspect the full child diff only for high-risk or surprising changes.
- Merge returned branches with `python3 <issue_workbench_dir>/scripts/integration_child.py merge <child_branch> --integration-branch <current_branch>`.
- On conflict, stop and report child issue, branch, worktree, and conflicted files.
- After each merge, run the smallest relevant validation command.
- Do not delete child worktrees automatically.
- Once multiple worktrees exist, use absolute paths for file-mutating commands.

Keep this compact state object in `.context/progress.md` after every child return or merge; store artifact paths, not pasted logs or full diffs:

```json
{"tracker":"#<parent>","mode":"integration","children":[{"issue":"#<n>","worktree":"/abs/path","branch":"issue-<n>","base":"<integration_branch>","commit":"<sha>","status":"returned|merged|needs_fix|pending_review","artifacts":{"progress_path":"/abs/path/.context/progress.md"},"pending_review":{}}],"checks":["<command>"],"current_step":"<next action>"}
```

### 3. Finish integration

- Re-inspect after every wave.
- If new non-final children are runnable, repeat Step 2.
- If non-final children have `pending_review`, resume those child worktrees at or after `poll_after_utc` and merge only after they return `review:"PASS"`.
- If non-final children remain blocked, pending, or missing and no independent child is runnable, stop and report blockers before `final_check`.
- Stop if the parent issue has no `final_check` child.
- Run `final_check` through `$issue-workbench` only after every non-final child is merged or otherwise done.
- Verification-only `final_check` children must not create empty commits; empty `diff_stat` plus `commit` equal to shipyard HEAD is the no-op completion signal.
- `final_check` may fix only final-check-owned docs/tests. Code defects must return `needs_child_fix:"#<issue>"`.
- Validate `final_check` with the same handoff JSON checks as any child. If it returns `PENDING_REVIEW`, record it and resume later; do not merge or enter final review. Skip merge for the no-op completion signal; otherwise merge its returned branch.

### 4. Final review and PR

- Run `$review-checkpoint` on the shipyard branch with `wait_mode=defer`.
- Classify each finding as `child:<issue>`, `final_check`, `integration`, `stale`, `non_actionable`, or `tooling_unavailable`.
- Route `child:<issue>` and `final_check` findings back to their recorded `$issue-workbench` worktrees, then merge the returned branch and rerun relevant checks.
- Fix only `integration` findings in the shipyard worktree: merge conflicts, PR body, progress scratch, or final assembly mistakes.
- Record `stale`, `non_actionable`, and `tooling_unavailable` findings and stop the fix loop for them. If Greptile fails once, accept `$review-checkpoint` fallback and do not retry Greptile.
- If the final review returns `PENDING_REVIEW`, record it and stop before PR publication until resume returns `PASS`.
- Run `$pr-launchpad` only after a completed final review gate returns `PASS`. Include close keywords for every child issue, including `final_check`. If `$review-checkpoint` used a Greptile-unavailable fallback, include its testing/review note in the PR body.

### 5. Route PR health

- Read checks with `gh pr checks`.
- Invoke `$ci-repairbay` for failing GitHub Actions checks.
- Invoke `$review-repairbay` for requested changes, unresolved threads, or inline comments. Execution mode is approval to fix/reply/resolve/re-fetch unless the user restricted GitHub writes.
- Ignore resolved, outdated, informational, approval, top-level summary, or waived unavailable external review checks.
- Stop on human approval, merge-permission, or external-provider blockers.

## Runtime Rules

- Batch one runnable integration wave in parallel; re-inspect before the next wave.
- Stop retrying Greptile after the first provider/tooling failure and run one fallback review.
- Avoid broad final `pytest` when a known readiness hang exists. Run targeted suites and record known skips.
- Do not apply patches for child-owned code from the shipyard worktree; route them to `$issue-workbench`.

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
