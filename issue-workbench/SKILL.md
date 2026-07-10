---
name: issue-workbench
description: Implement one GitHub issue in a guarded feature branch. Use when asked to build or fix one issue, run review-checkpoint, publish a PR, or return shipyard integration JSON.
---

# issue-workbench

## Goal

Implement one GitHub issue into a clean feature branch with the smallest intentional diff.
Child implementation and actionable review fixes belong here, not in `$shipyard`.
Run `$review-checkpoint`; it owns Greptile, fallback review, blocker-only actionability rules, and contradictory-blocker handling.
After the latest completed review gate passes with no later commit, hand off to `pr-launchpad` unless `handoff_mode=integration_branch`.

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
- `max_iterations` is optional and passes through to `$review-checkpoint`.
- `review_base` is optional and passes through to `$review-checkpoint`; default is the branch base selected during branch preparation.
- `wait_mode` is optional and passes through to `$review-checkpoint`.
- `poll_interval_seconds` is optional and passes through to `$review-checkpoint`.
- `worktree_path` is optional. When set, create the issue branch in that new Git worktree instead of the caller worktree.
- `handoff_mode` is optional and defaults to `pull_request`. The only other supported value is `integration_branch`.
- `integration_branch` is required when `handoff_mode=integration_branch` and is the local branch that the issue branch will be merged back into by `$shipyard`.

## Scope and boundaries

### Lite mode

`$issue-workbench #<issue>` is the default path for one known actionable GitHub issue.

Use lite mode when:
- the issue already has enough acceptance criteria to implement,
- no dependency graph or parallel child work is needed,
- no integration branch is requested.

Do not invoke `$issue-blueprint`, `$shipyard`, create a parent issue, create child issues, or create a `final_check` in lite mode. Stop only when the issue lacks actionable acceptance criteria, product behavior is unclear, repo state is dirty, or the requested change would require unrelated refactoring.

### Boundaries

- Only modify files required by the issue.
- Do not perform unrelated refactors.
- Do not modify secrets, env files, generated files, lockfiles, `.agents/`, or infrastructure files unless the issue explicitly requires it or the review gate directly identifies a deterministic issue in that file.
- Do not add backward compatibility, migration layers, aliases, fallback paths, or future-proofing unless explicitly required by the issue, spec, or repo instructions.
- Do not fix sibling or newly discovered work inside the current issue; record it as a blocker, follow-up, or decision candidate instead.
- Do not modify `.context/` except local uncommitted progress, review, memory context, decision, and handoff artifacts referenced from `.context/progress.md`; keep `.context/progress.md` to `goal`, `current_step`, `artifacts`, `blockers`, and `validation`.
- Do not use `git add .` unless the full diff has been inspected.
- Use Conventional Commits.
- Return only the PR URL on success unless `handoff_mode=integration_branch`.
- Stop instead of guessing when the issue is not actionable, requires a product decision, or would require forbidden-path changes not explicitly required by the issue.

## Procedure

### 1. Confirm clean working tree

```bash
git status --short
```

Stop on existing uncommitted changes unless the user explicitly asked to continue with them. Do not overwrite or discard user changes.

### 2. Read memory context if configured

If `agent-memory` is configured for the repo, run:

```bash
python3 <agent_memory_dir>/scripts/memory_context.py --project-root . --issue <issue_number> --out .context/memory-context.md
```

Read `.context/memory-context.md` only when the command loaded notes. If the command cannot resolve a memory router, continue without memory context; do not block implementation.

### 3. Read the issue

Run:

```bash
python3 <skill_dir>/scripts/issue_snapshot.py <issue_number>
```

If truncation or omitted comments hide context needed to decide scope, rerun it with larger limits before implementing.

Extract explicit requirements, acceptance criteria, constraints, named files, named modules, and named behavior. Use that as the implementation scope. Do not invent product behavior.

### 4. Prepare the branch

Use the current worktree by default. In `handoff_mode=integration_branch`, require `worktree_path` and `integration_branch`, then use the integration helper.

Use the helper for normal PR mode:

```bash
python3 <skill_dir>/scripts/start_issue_branch.py <issue_number> [--base-branch <base_branch>] [--branch-slug <branch_slug>]
```

For `$shipyard` integration mode:

```bash
python3 <skill_dir>/scripts/integration_child.py start <issue_number> --worktree-path <worktree_path> --integration-branch <integration_branch> [--branch-slug <branch_slug>]
```

The child branch must start from `integration_branch`, not the repository default branch. After setup, `cd` into the returned worktree and keep the caller worktree branch unchanged.

Resolve `<review_base>` from the `review_base` input when provided; otherwise use `<integration_branch>` in integration mode and `origin/<base_branch>` in PR mode. If repo instructions require `.context/progress.md`, `integration_child.py start` initializes the five-field progress object and records any prior progress file under `artifacts.source_progress`; keep it uncommitted.

### 5. Inspect the repository before editing

Identify the smallest relevant files or modules with `rg` or `rg --files`. Prefer existing patterns, tests, helpers, and conventions. Avoid new dependencies unless the issue requires them.

### 6. Select the testing seam

Before editing tests, identify the public behavior boundary:

- Seam: public interface under test, or `none` with reason.
- Existing similar tests: paths or `none found`.
- Validation command: smallest meaningful command, or `none obvious`.
- Do not test: internals, mocks, or implementation details that would couple the test to the chosen design.

If no useful test seam exists, use another concrete validation path. Do not invent low-value tests.

### 7. Implement

Apply the smallest code change that satisfies the issue. Add or update tests only when they directly validate requested behavior.

### 8. Inspect the diff

```bash
git status --short
git diff --stat
git diff
python3 <issue_workbench_dir>/scripts/diff_guard.py --base <review_base>
```

`diff_guard.py` includes untracked files. If a new file should appear in `git diff --stat` before staging, run `git add -N <path>` and rerun the diff/stat commands.

If the issue explicitly requires a blocked path, verify that requirement in the issue text, then rerun the guard with `--base <review_base> --allow <path>`. Stop if any changed file or line cannot trace to the issue.

### 9. Run relevant local validation

Run the smallest relevant validation command discoverable from nearby tests, `package.json`, `pyproject.toml`, `tox.ini`, `noxfile.py`, `pytest.ini`, or `Makefile`. If no command is obvious, continue without inventing tooling.

### 10. Commit

```bash
git add <file1> <file2>
```

Stage explicit inspected paths only. Commit one logical unit at a time:

```bash
git commit -m "feat(auth): add token refresh handling"
```

### 11. Review gate

Run `$review-checkpoint` with the selected `review_base`, `max_iterations`, `wait_mode`, and `poll_interval_seconds`. It owns review provider selection, fallback review, blocker-only actionability rules, fix loops, and review-loop commits.

If it returns `PENDING_REVIEW`, do not treat it as `PASS`. In `handoff_mode=pull_request`, stop and report `PENDING_REVIEW` with the pending state location. In `handoff_mode=integration_branch`, return pending handoff JSON in final handoff.

If it returns anything other than `PASS` or `PENDING_REVIEW`, stop with its status and artifact path. Continue only after the latest completed review gate returns `PASS` with no later commit.

After a `PASS`, rerun the path guard before handoff:

```bash
python3 <issue_workbench_dir>/scripts/diff_guard.py --base <review_base>
```

If the guard fails, stop unless the issue explicitly allows that path or `$review-checkpoint` directly identified a deterministic issue in that blocked path; verify the finding before allowing the path.

### 12. Record durable decisions

If implementation created or confirmed a durable decision future agents need, append one structured candidate instead of writing Obsidian directly:

```bash
python3 <agent_memory_dir>/scripts/append_decision.py --project-root . --topic <topic> --decision "<decision>" --reason "<why>" --source "issue #<issue_number>"
```

Skip routine progress, passing checks, and ordinary implementation details.

### 13. Final handoff

Do not duplicate final branch, diff, or PR checks. `pr-launchpad` owns PR-mode inspection, and `integration_child.py finish` owns integration-mode branch, clean-worktree, merge-base, commit, changed-files, and diff-stat reporting. `.context/progress.md` may remain local and uncommitted.

If `handoff_mode=pull_request`, run `pr-launchpad` only after a completed review gate returns `PASS`, then return only the PR URL.

Before returning in integration mode, keep only `goal`, `current_step`, `artifacts`, `blockers`, and `validation` in `.context/progress.md`; store detailed notes, validation output, review state, and resume hints only when needed. Do not write a per-child handoff file. The response is the child handoff JSON.

If `handoff_mode=integration_branch` and the review gate returned `PASS`, do not run `pr-launchpad`. Return only the JSON object emitted by `integration_child.py finish`:

```bash
python3 <skill_dir>/scripts/integration_child.py finish --review-base <review_base> --verification pass:<summary> --review PASS --check "<cmd>" --known-skip "<reason>"
```

The JSON includes `issue`, `branch`, `worktree`, `base_ref`, `base_sha`, `commit`, `head_sha`, `changed_files`, `diff_stat`, `verification`, `review`, `checks`, `known_skips`, and `artifacts.progress_path`; `review` must be `PASS` unless `pending_review` or `needs_child_fix:"#<issue>"` is present.

If `handoff_mode=integration_branch` and the review gate returned `PENDING_REVIEW`, return handoff JSON with `issue`, `branch`, `worktree`, `base_ref`, `base_sha`, `commit`, `head_sha`, `changed_files`, `diff_stat`, `verification`, `review:"PENDING_REVIEW"`, `checks`, `known_skips`, `artifacts.progress_path`, and `pending_review` copied from the five-field `.context/progress.md` object or an artifact it references. Include at least `review_id`, `branch`, `local_head_sha`, `upstream_sha`, `base_ref`, `base_sha`, `poll_after_utc`, and `progress_path`; do not call `integration_child.py finish` or set `review` to `PASS`.

For a verification-only `final_check` child, do not create an empty commit. It may fix only final-check-owned docs/tests. If it finds an implementation defect owned by a child issue, do not fix it there; return `review:"FAIL"` and `needs_child_fix:"#<issue>"` so `$shipyard` routes it back:

```bash
python3 <skill_dir>/scripts/integration_child.py finish --review-base <review_base> --verification skip:needs-child-fix --review FAIL --needs-child-fix '#123'
```

An empty `diff_stat` with `commit` equal to the integration branch HEAD is the no-op completion signal for `$shipyard`.

## Output

Return only the PR URL in normal mode, `PENDING_REVIEW` with its progress path when normal mode is deferred, or the compact handoff JSON in integration mode. Do not include markdown, logs, copied diffs, or extra summaries.
