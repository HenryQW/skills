---
name: issue-workbench
description: Implement one GitHub issue in a guarded feature branch. Use when asked to build or fix one issue, run review-checkpoint, publish a PR, or return a Shipyard integration handoff path.
---

# issue-workbench

## Goal

Implement one GitHub issue into a clean feature branch with the smallest intentional diff. Child implementation and actionable review fixes belong here, not in `$shipyard`. `$review-checkpoint` owns review selection, blocker actionability, and contradictory-blocker handling; after its latest completed `PASS` with no later commit, hand off to `pr-launchpad` unless `handoff_mode=integration_branch`.

## Bundled resources

- `scripts/issue_snapshot.py`: compact issue text and comments.
- `scripts/branch_name.py`: deterministic branch names.
- `scripts/start_issue_branch.py`: branch and shipyard worktree setup.
- `scripts/integration_child.py`: integration-mode start, finish, and merge glue.
- `scripts/diff_guard.py`: forbidden-path guard.

Use `<issue_workbench_dir>` as the absolute path to this skill directory when running `diff_guard.py`.

## Inputs

- `issue_number` is required.
- `base_branch` is optional and defaults to the repository default branch.
- `branch_slug` is optional.
- `max_iterations`, `review_base`, `wait_mode`, and `poll_interval_seconds` pass through to `$review-checkpoint`; `review_base` defaults to the branch base selected during preparation.
- `worktree_path` is optional. When set, create the issue branch in that new Git worktree instead of the caller worktree.
- `handoff_mode` is optional and defaults to `pull_request`. The only other supported value is `integration_branch`.
- `integration_branch` is required when `handoff_mode=integration_branch` and is the local branch that the issue branch will be merged back into by `$shipyard`.

## Scope and boundaries

### Lite mode

`$issue-workbench #<issue>` is the default for an issue with actionable acceptance criteria, no dependency graph or parallel work, and no integration branch. Do not invoke `$issue-blueprint`, `$shipyard`, parent/child issues, or `final_check`. Stop when acceptance criteria or product behavior are unclear, repo state is dirty, or the change needs unrelated refactoring.

### Boundaries

- Only modify files required by the issue.
- Do not perform unrelated refactors.
- Do not modify secrets, env files, generated files, lockfiles, `.agents/`, or infrastructure files unless the issue explicitly requires it or the review gate directly identifies a deterministic issue in that file.
- Do not add compatibility, migration, aliases, fallback paths, or future-proofing unless explicitly required; record sibling or newly discovered work as a blocker, follow-up, or decision candidate.
- Do not modify `.context/` except local uncommitted progress, review, memory context, decision, and handoff artifacts referenced from `.context/progress.md`; keep `.context/progress.md` to `goal`, `current_step`, `artifacts`, `blockers`, and `validation`.
- In integration mode, do not send interim status messages to Shipyard; return only the canonical handoff path.
- Do not use `git add .` unless the full diff has been inspected.
- Use Conventional Commits.
- Stop instead of guessing when the issue is not actionable, requires a product decision, or would require forbidden-path changes not explicitly required by the issue.

## Procedure

### 1. Load memory context if configured

When invoked directly, invoke `$agent-memory load` with the issue scope; continue on `memory_load=SKIPPED` and do not run setup. In integration mode, `$shipyard` owns this boundary.

### 2. Confirm clean working tree

```bash
git status --short
```

Stop on existing uncommitted changes unless the user explicitly asked to continue with them. Do not overwrite or discard user changes.

### 3. Read the issue

Run:

```bash
python3 <skill_dir>/scripts/issue_snapshot.py <issue_number>
```

If `[truncated]` or omitted comments hide scope, rerun with larger limits before implementing. Extract explicit requirements, acceptance criteria, constraints, named files/modules, and behavior; do not invent product behavior.

### 4. Prepare the branch

Use the current worktree by default. `handoff_mode=integration_branch` requires `worktree_path` and `integration_branch`.

Use the helper for normal PR mode:

```bash
python3 <skill_dir>/scripts/start_issue_branch.py <issue_number> [--base-branch <base_branch>] [--branch-slug <branch_slug>]
```

For `$shipyard` integration mode:

```bash
python3 <skill_dir>/scripts/integration_child.py start <issue_number> --worktree-path <worktree_path> --integration-branch <integration_branch> [--branch-slug <branch_slug>]
```

The child branch starts from `integration_branch`, not the repository default; `cd` into the returned worktree and leave the caller branch unchanged.

Resolve `<review_base>` from the `review_base` input when provided; otherwise use `<integration_branch>` in integration mode and `origin/<base_branch>` in PR mode. If repo instructions require `.context/progress.md`, `integration_child.py start` initializes the five-field progress object and records any prior progress file under `artifacts.source_progress`; keep it uncommitted.

### 5. Inspect the repository before editing

Identify the smallest relevant files or modules with `rg`/`rg --files`; prefer existing patterns, tests, helpers, and conventions. Avoid dependencies unless required.

### 6. Select the testing seam

Before editing tests, identify the public behavior boundary:

- Seam: public interface under test, or `none` with reason.
- Existing similar tests: paths or `none found`.
- Validation command: smallest meaningful command, or `none obvious`.
- Do not test: internals, mocks, or implementation details that would couple the test to the chosen design.

If no useful test seam exists, use another concrete validation path; do not invent low-value tests.

### 7. Implement

Apply the smallest code change that satisfies the issue. Add or update tests only when they directly validate requested behavior.

### 8. Inspect the diff

```bash
git status --short
git diff --stat
git diff
python3 <issue_workbench_dir>/scripts/diff_guard.py --base <review_base>
```

`diff_guard.py` includes untracked files; use `git add -N <path>` to include a new file in diff/stat before staging. For an explicitly required blocked path, verify the issue text, then rerun with `--allow <path>`. Stop if any changed file or line cannot trace to the issue.

### 9. Run relevant local validation

Run the smallest relevant command discoverable from nearby tests or project config; if none is obvious, continue without inventing tooling.

### 10. Commit

```bash
git add <file1> <file2>
```

Stage explicit inspected paths only. Commit one logical unit at a time:

```bash
git commit -m "feat(auth): add token refresh handling"
```

### 11. Review gate

Run `$review-checkpoint` with the selected `review_base`, `max_iterations`, `wait_mode`, and `poll_interval_seconds`. In integration mode, do not pass Shipyard's shared manifest: the child records isolated review state and returns it through this handoff.

If it returns `PENDING_REVIEW`, do not treat it as `PASS`. In `handoff_mode=pull_request`, stop and report `PENDING_REVIEW` with the pending state location. In `handoff_mode=integration_branch`, run `integration_child.py finish --review PENDING_REVIEW`; it writes the pending state into the canonical handoff file.

Otherwise, stop with its status and artifact path. Continue only after the latest completed review gate returns `PASS` with no later commit.

After a `PASS`, rerun the path guard before handoff:

```bash
python3 <issue_workbench_dir>/scripts/diff_guard.py --base <review_base>
```

If the guard fails, stop unless the issue explicitly allows that path or `$review-checkpoint` directly identified a deterministic issue in that blocked path; verify the finding before allowing the path.

### 12. Record durable decisions

For a durable decision future agents need, append one structured candidate instead of writing Obsidian directly:

```bash
python3 <agent_memory_dir>/scripts/append_decision.py --project-root . --topic <topic> --decision "<decision>" --reason "<why>" --source "issue #<issue_number>"
```

Skip routine progress, passing checks, and ordinary implementation details.

### 13. Final handoff

Do not duplicate final branch, diff, or PR checks: `pr-launchpad` owns PR-mode inspection; `integration_child.py finish` owns integration-mode reporting. `.context/progress.md` may remain local and uncommitted. Return only the PR URL, deferred `PENDING_REVIEW` progress path, or integration handoff path—no markdown, logs, diffs, or summaries.

In `pull_request` mode, invoke nested `pr-launchpad` only after `PASS` (it skips its memory boundary), then `$agent-memory distill`. Distill before every terminal return, including `Stop`, `Blocked`, and `PENDING_REVIEW`; in integration mode, do not distill and preserve `.context/decisions.jsonl` for `$shipyard`.

Before returning in integration mode, keep only `goal`, `current_step`, `artifacts`, `blockers`, and `validation` in `.context/progress.md`; detailed notes, output, review state, and resume hints are optional. `integration_child.py finish` writes canonical `.context/integration-handoff.json` and records its absolute path in `artifacts.handoff`.

If `handoff_mode=integration_branch` and the review gate returned `PASS`, do not run `pr-launchpad`. Emit the output of:

```bash
python3 <skill_dir>/scripts/integration_child.py finish --review-base <review_base> --verification pass:<summary> --review PASS --check "<cmd>" --known-skip "<reason>"
```

Return only the helper's absolute path. Its file is authoritative: do not reconstruct, copy, or extend its factual JSON or select a Shipyard child status.

If `handoff_mode=integration_branch` and the review gate returned `PENDING_REVIEW`, keep its evidence under `.context/progress.md` `artifacts.pending_review`. It must include `review_id`, `branch`, `local_head_sha`, `upstream_sha`, `base_ref`, `base_sha`, `poll_after_utc`, and `progress_path`. Then run:

```bash
python3 <skill_dir>/scripts/integration_child.py finish --review-base <review_base> --verification skip:review-pending --review PENDING_REVIEW
```

If validation or review finds an implementation defect owned by another child issue, do not fix it here; run:

```bash
python3 <skill_dir>/scripts/integration_child.py finish --review-base <review_base> --verification skip:needs-child-fix --review FAIL --needs-child-fix '#123'
```
