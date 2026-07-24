---
name: issue-workbench
description: Implement one GitHub issue in a guarded feature branch. Use when asked to build or fix one issue, run review-checkpoint, publish a PR, or return a Shipyard integration handoff path.
---

# Issue Workbench

Implement one actionable issue with the smallest intentional diff. `$review-checkpoint` owns blocker actionability; `$pr-launchpad` owns PR publication; Shipyard owns integration.

## Inputs

- `issue_number` is required.
- `base_branch` defaults to the repository default; `branch_slug` is optional.
- `worktree_path` is optional in pull-request mode and is prepared by Shipyard in integration mode.
- `max_iterations`, `review_base`, `wait_mode`, and `poll_interval_seconds` pass through to `$review-checkpoint`.
- `handoff_mode` is `pull_request` (default) or `integration_branch`.
- `integration_branch` and Shipyard's prepared `worktree_path` are required in integration mode.

## Memory

Direct invocation owns issue-scoped `$agent-memory`; integration mode defers it
to Shipyard.

## Boundaries

- Default lite mode handles one issue only; do not invoke Blueprint, Shipyard, parent/child planning, or `final_check`.
- Stop on unclear acceptance or product behavior, unrelated dirty changes, forbidden-path changes not explicitly required, or required unrelated refactoring.
- Modify only issue-owned files. Do not touch secrets, env, generated, lock, `.agents/`, infrastructure, or `.context/` files unless explicitly required or a verified review blocker requires it.
- `.context/` may contain only local progress, review, memory, decision, and handoff artifacts. Keep progress to `goal`, `current_step`, `artifacts`, `blockers`, and `validation`; never commit it.
- Do not add compatibility, migration, aliases, fallbacks, dependencies, or future-proofing without an explicit requirement. Use Conventional Commits and stage only inspected paths.
- Integration children send no interim status and never run `pr-launchpad`.

## Workflow

1. In integration mode, enter Shipyard's existing `worktree_path`; require its current branch to match `issue-<issue_number>(-<slug>)?`, require `integration_branch` to be its ancestor, and never create or switch the child branch. Then require a clean worktree and read the issue with:

   ```bash
   python3 <skill_dir>/scripts/issue_snapshot.py <issue_number>
   ```

   If truncation hides scope, rerun with larger limits. Extract requirements and constraints; do not invent behavior.

2. In pull-request mode, prepare the branch with:

   ```bash
   python3 <skill_dir>/scripts/start_issue_branch.py <issue_number> [--base-branch <base_branch>] [--branch-slug <branch_slug>] [--worktree-path <worktree_path>]
   ```

   `review_base` defaults to `integration_branch` in integration mode and `origin/<base_branch>` otherwise. Preserve any initialized five-field progress file.

3. Inspect relevant code, callers, existing patterns, and tests. Select the public behavior seam and smallest meaningful validation; do not add implementation-detail tests when no useful seam exists. Implement only the issue.

4. Inspect the complete diff and run the path guard, which includes untracked files:

   ```bash
   git status --short
   git diff --stat
   git diff
   python3 <skill_dir>/scripts/diff_guard.py --base <review_base>
   ```

   Use `git add -N` for new files. Allow a blocked path only after tracing it to an explicit issue requirement or verified review blocker. Run the smallest relevant validation, commit inspected paths, bind its command and result to `validated_head=$(git rev-parse HEAD)`, and push the initial review `HEAD` (`git push --set-upstream origin HEAD` when needed).

5. Capture `pre_review_head`, then run `$review-checkpoint` with `mode=fix_loop`, `review_base`, `max_iterations`, `wait_mode`, and `poll_interval_seconds`; do not pass Shipyard's shared manifest from a child worktree. Return `BLOCKED` or `PENDING_REVIEW` with its artifact instead of treating either as PASS. Continue only after the latest completed review returns `PASS` with no later commit. If `HEAD` changed, rerun `diff_guard.py` and use the review fix's check evidence for the new `validated_head`; otherwise reuse Step 4 evidence.

6. Finish according to mode.

## Handoff

In pull-request mode, a `PENDING_REVIEW` returns its pending state path. After
`PASS`, invoke nested `$pr-launchpad` with `validated_head` and its validation
commands/results, then return only the PR URL.

In integration mode, pass inspected facts to the helper; it writes the canonical `.context/integration-handoff.json` through Shipyard's manifest interface:

```bash
# PASS
python3 <skill_dir>/scripts/integration_child.py finish --review-base <review_base> --review PASS --check "<cmd>" --known-skip "<reason>"

# deferred review
python3 <skill_dir>/scripts/integration_child.py finish --review-base <review_base> --review PENDING_REVIEW

# defect owned by another child
python3 <skill_dir>/scripts/integration_child.py finish --review-base <review_base> --review FAIL --needs-child-fix '#123'
```

For `PENDING_REVIEW`, retain the checkpoint evidence under `artifacts.pending_review`. Return only the helper's absolute path; never reconstruct, copy, or extend its payload or choose a Shipyard child status.
