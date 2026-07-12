---
name: shipyard
description: Orchestrate a dependency-aware parent issue from its deterministic integration branch into one final PR. Use for issue-blueprint parent issues that need child worktrees, merges, final_check, checks, reviews, and PR routing.
---

# Shipyard

## Overview

Advance one dependency-aware parent issue without copying the child skills' work.
Shipyard is orchestration only: inspect the graph, launch child worktrees, merge returned child branches, run integration checks, classify final review blockers, and create the final PR.
`$issue-workbench`, `$ci-repairbay`, `$review-repairbay`, `$review-checkpoint`, and `$pr-launchpad` own implementation, actionable review fixes, CI, review comments, review gates, and PR creation.

Shipyard has one execution mode:

- `$shipyard #123` or `shipyard #123` means execute parent issue `#123`.
- Reconcile to the parent-derived shipyard integration branch before creating child worktrees, branches, commits, merges, or PRs.
- Inspect-only behavior is allowed only when the user explicitly asks to inspect, plan, dry-run, or report without executing.

## Memory Boundary

- Shipyard owns the memory boundary when the user invokes it directly: call `$agent-memory load` before Preflight and `$agent-memory distill` as the final guard before every terminal return, including inspect-only, dirty-worktree, dependency, review, approval, CI, and successful PR outcomes.
- Invoke child, review, repair, and PR skills as nested workflows with their memory boundaries skipped. They must preserve durable candidates for Shipyard.
- Append only durable cross-child decisions, accepted integration constraints, and reusable root causes. Do not capture child status, checks, review IDs, or transient blockers.
- Memory failure must not replace the Shipyard result or stop reason.

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
- `scripts/manifest.py`: maintains `.context/shipyard-manifest.json`, the
  trusted run artifact. It alone encodes and validates child handoffs, maps
  them into lifecycle transitions, owns validation and review-event schemas,
  and rewrites `.context/progress.md` as its pointer.
- `<issue_workbench_dir>/scripts/integration_child.py`: starts child worktrees, supplies inspected Git and review facts to the installed Shipyard manifest interface, and merges returned child branches; resolve `<issue_workbench_dir>` from the loaded `issue-workbench` skill path.

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
- Initialize `.context/shipyard-manifest.json` with `python3 <shipyard_dir>/scripts/manifest.py init <parent_issue> <current_branch> --base-branch <default_branch>`.
- Do not launch the first child until manifest init succeeds.
- Read only issue-linked docs or named files needed to understand runnable children.

### 2. Run one wave

- Ensure the shipyard worktree is clean.
- Use the current branch as the integration branch.
- Run only current non-final children with status `runnable`; do not pre-create blocked children.
- Choose deterministic sibling worktree paths such as `../<repo>-shipyard-<parent_issue>-child-<child_issue>` and stop if a path already exists.
- Start each child with `python3 <issue_workbench_dir>/scripts/integration_child.py start <child_issue> --worktree-path <absolute_child_worktree> --integration-branch <current_branch>`.
- Spawn each child with `fork_turns=none`; the prompt below is its complete context. Launch a runnable wave in parallel, but use `wait_mode=block` for every child. Use `defer` only when the user explicitly requests resumable coordination; a block-mode timeout may still return `PENDING_REVIEW`.
- Launch children in parallel with this prompt:

```text
Use $issue-workbench <child_issue>
worktree_path=<absolute_child_worktree>
handoff_mode=integration_branch
integration_branch=<current_branch>
review_base=<current_branch>
wait_mode=block
handoff_path=<absolute_child_worktree>/.context/integration-handoff.json
```

- Do not send status probes to running children. Wait for completion notifications and keep user updates phase-level.
- Read the returned handoff and ingest it with `python3 <shipyard_dir>/scripts/manifest.py ingest-child --file <child_handoff_file>`.
  The same manifest interface encoded the canonical bytes and now decodes the
  handoff into its child lifecycle transition. Stop on its error rather than
  copying, reconstructing, or validating the JSON elsewhere.
- If the child worktree has `.context/decisions.jsonl`, re-append each durable record to the Shipyard root with `<agent_memory_dir>/scripts/append_decision.py`; stable IDs deduplicate repeats. Do not write Obsidian or ask `pr-launchpad` to distill.
- If `needs_child_fix` is present, stop shipyard edits and rerun or reuse `$issue-workbench` in that child worktree.
- If `review` is `PENDING_REVIEW`, do not merge the branch and continue other runnable independent children when available.
- Spot-check `diff_stat`; inspect the full child diff only for high-risk or surprising changes.
- Merge returned branches with `python3 <issue_workbench_dir>/scripts/integration_child.py merge <child_branch> --integration-branch <current_branch> --expected-commit <commit>`.
- After each successful merge, run `python3 <shipyard_dir>/scripts/manifest.py merge-child <child_issue> --commit <commit>`.
- On conflict, stop and report child issue, branch, worktree, and conflicted files.
- Run one manifest/branch check before merge, one smallest relevant validation after the merge or wave, and one final validation before PR. Do not repeat `git status`, manifest validation, or issue inspection after every manifest update.
- Do not delete child worktrees automatically.
- Once multiple worktrees exist, use absolute paths for file-mutating commands.

### 3. Finish integration

- Re-inspect after every wave.
- If new non-final children are runnable, repeat Step 2.
- If non-final children have `pending_review`, resume those child worktrees at or after `poll_after_utc` and merge only after they return `review:"PASS"`.
- If non-final children remain blocked, pending, or missing and no independent child is runnable, stop and report blockers before `final_check`.
- Stop if the parent issue has no `final_check` child.
- Treat `final_check` as verification-only. Read its named integration commands and run them directly on the clean integration branch after every non-final child is merged. Do not launch a child or review for it, and do not edit code.
- If a command fails, route the defect to the child whose acceptance criterion owns it. Stop for user direction when ownership is unclear.
- Record final-check evidence through `python3 <shipyard_dir>/scripts/manifest.py set-validation --file <event_file>`; `manifest.py` validates the SHA-bound event and checks.
- On resume, skip `final_check` only when `validation_plan.final.issue` matches it and `validation_plan.final.head_sha` equals current `HEAD`.

### 4. Final review and PR

- Run exactly one mandatory review gate: `$review-checkpoint` as a nested workflow on the shipyard branch with `wait_mode=block`, `manifest_path=<absolute_path_to_.context/shipyard-manifest.json>`, and its memory boundary skipped.
- Do not run `greptile review`, poll Greptile, or write manifest review events by hand; `$review-checkpoint` owns that loop.
- If it returns blockers for Shipyard to route, classify each as `child:<issue>`, `final_check`, `integration`, `stale`, `non_actionable`, or `tooling_unavailable`.
- Route `child:<issue>` blockers back to their recorded `$issue-workbench` worktrees. Treat `final_check` blockers as failed verification and route them to the child that owns the failed acceptance criterion; stop for user direction when ownership is unclear. Ingest repaired PASS handoffs, merge returned branches, record `merge-child`, and rerun relevant checks.
- Fix only `integration` blockers in the shipyard worktree: merge conflicts, PR body, progress scratch, or final assembly mistakes.
- Record `stale`, `non_actionable`, and `tooling_unavailable` findings and stop the fix loop for them. Do not route another review loop for non-blocking findings.
- If the final review returns `PENDING_REVIEW`, record it and stop before PR publication until resume returns `PASS`.
- After a review fix commit, rerun the final-check commands and replace the SHA-bound validation event.
- Run `python3 <shipyard_dir>/scripts/manifest.py --manifest <manifest_path> can-reuse $(git rev-parse HEAD)`. Run `$pr-launchpad` only after it succeeds. Pass `shipyard_manifest=<absolute_path_to_.context/shipyard-manifest.json>` and skip its memory boundary so PR launch consumes child issues, final-check evidence, checks, commits, skips, and close targets without reconstructing them.

### 5. Route PR health

- After PR creation, do one PR health snapshot with `gh pr checks` or the repository's normal PR check command. Do not sleep-and-recheck unless a repair skill changed branch or PR state.
- Read checks only to choose the first repair skill.
- Invoke `$ci-repairbay` as a nested workflow with its memory boundary skipped for failing GitHub Actions checks.
- Invoke `$review-repairbay` as a nested workflow with its memory boundary skipped for requested changes, unresolved threads, or inline comments. Execution mode is approval to fix/reply/resolve/re-fetch unless the user restricted GitHub writes.
- After invoking a repair skill, trust its `status=PASS|BLOCKED|PENDING` line; re-check only if the status is missing or inconsistent.
- Ignore resolved, outdated, informational, approval, top-level summary, or waived unavailable external review checks.
- Stop on human approval, merge-permission, or external-provider blockers.

## Runtime Rules

- Batch one runnable integration wave in parallel; re-inspect before the next wave.
- Avoid broad final `pytest` when a known readiness hang exists. Run targeted suites and record known skips.
- Do not apply patches for child-owned code from the shipyard worktree; route them to `$issue-workbench`.
- Do not store full diffs by default. Store `base_ref`, `base_sha`, `commit`, `head_sha`, `changed_files`, and `diff_stat`; create `.context/review-payload.txt` only when a review subagent needs an artifact it cannot reproduce from git.
- If review history must survive handoff, use one `.context/review-events.jsonl`; do not create per-child or per-review artifact folders.

## State Rules

- The GitHub parent issue is the durable source of truth.
- Child issue bodies define dependencies; PR state defines implementation progress.
- `.context/shipyard-manifest.json` is the single trusted local run artifact;
  `.context/progress.md` only points to it.
- A child is `done-local` for the current run only after its branch is merged into the shipyard branch. This clears its blocker for the run; do not run it again even if its issue remains open.
- Durable completion requires the child's PR to merge or its issue to close. For `done-local` children, merging the final shipyard PR is the durable completion signal.

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
- Manifest path and PR URL when available.
- CI/review routing performed.
- Verification commands actually run.
- Current stop reason and next runnable issue, if any.
