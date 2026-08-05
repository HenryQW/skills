---
name: shipyard
description: Orchestrate a dependency-aware parent issue from its deterministic integration branch into one final PR. Use for issue-blueprint parent issues that need child worktrees, merges, final_check, checks, reviews, and PR routing.
---

# Shipyard

Execute an Issue Blueprint parent graph without duplicating child work. Workbench implements and repairs children; Review Checkpoint owns the review gate; CI and Review Repairbay own PR health; Launchpad creates the PR.

## Inputs and mode

- `parent_issue` is required as a GitHub issue number or URL.
- `--integration-worktree` optionally selects an existing absolute worktree path.
- Normalize `parent_issue` once to numeric `parent_id`, accepting `123`, `#123`, or a GitHub issue URL. Use only `parent_id` for branch naming, inspection, and manifest commands.
- Infer repository from the GitHub remote, base from the repository default, and the integration branch with `issue-workbench/scripts/branch_name.py integration <parent_id>`.
- Execute by default. Inspect-only behavior requires an explicit inspect, plan, dry-run, or report request.

Direct invocation owns `$agent-memory`; nested skills defer it to Shipyard.

## State and ownership

- The parent issue is durable truth; child bodies define dependencies and PRs define durable implementation progress.
- `.context/shipyard-manifest.json` is the single trusted local run artifact; `manifest.py` alone validates handoffs, lifecycle transitions, validation, and review events. `.context/progress.md` only points to it.
- A child is `done-local` after its recorded branch is merged into the integration branch. Merging the final Shipyard PR makes that completion durable.
- Load each nested skill once, immediately before first use. Query manifest coordination as `issue`, `head_sha`, `status`, and `checks`; inspect full diffs only for incomplete or surprising evidence or merge conflicts.
- A frozen wave is one issue set plus `wave_base_sha`: no child merges until every handoff is `PASS` without `needs_child_fix` and every retained base still matches; then all merge in ascending issue order. Pending or failed work keeps the whole wave unmerged.
- Validation and review evidence are HEAD-bound; any code-changing repair invalidates evidence for the prior HEAD.

## 1. Preflight

1. If provided, require an absolute integration worktree and enter it. Require a clean worktree, fetch remotes, and resolve the default and expected integration branches. Switch to an existing local/remote expected branch; otherwise rename a current non-default branch with no upstream, or create the expected branch from the remote/default base. Never rename the default branch.
2. Run `scripts/inspect_parent_issue.py <parent_id> --json`. Stop if it cannot resolve the parent, branch policy, graph, `final_check`, or runnable state; report `mode=default_branch_blocked` rather than executing on the default branch.
3. Initialize the manifest before launching children:

   ```bash
   python3 <shipyard_dir>/scripts/manifest.py init <parent_id> <integration_branch> --base-branch <default_branch>
   ```

Read only issue-linked or named material needed for runnable children.

## 2. Run a frozen wave

1. From the clean integration branch, select the ascending set of current runnable non-final children. Capture that exact set and `wave_base_sha=$(git rev-parse HEAD)`; neither may change before the complete wave is integrated.
2. For each child, require an absent deterministic sibling path, then run `integration_child.py start <issue> --worktree-path <path> --integration-branch <integration_branch>` to create a clean worktree on a new branch from `integration_branch` at `wave_base_sha`. A path removed after an earlier wave may be reused. Spawn children in parallel with `fork_turns=none` using this complete contract:

   ```text
   Use $issue-workbench <child_issue>
   worktree_path=<absolute_child_worktree>
   handoff_mode=integration_branch
   integration_branch=<integration_branch>
   ```

   Workbench enters the prepared worktree and runs the child's native subagent review gate; it never creates the worktree or launches a PR. Do not probe running children or remove running, failed, conflicted, or otherwise unmerged worktrees; use absolute paths for mutations once multiple worktrees exist.
3. Ingest every returned handoff directly into the canonical manifest through `manifest.py ingest-child --file <path>` as it returns. `manifest.py` validates it; never reconstruct or separately validate its JSON. Re-append durable child decisions through Agent Memory's append helper.
4. Enforce the frozen-wave barrier. Rerun an unmerged owning Workbench child for review fixes. If a defect belongs to a `done-local` predecessor, follow Repair waves. Stop on base drift; never refresh the wave base or children.
5. Merge the complete PASS wave with `integration_child.py merge ... --expected-head <head_sha>`, recording each success through `manifest.py merge-child --head-sha <head_sha>`. Do not validate, re-inspect, reopen diffs, or print detail between merges. Preserve earlier successful merges if a later child conflicts; stop with that child's issue, branch, worktree, and conflicted files.
6. After the complete wave is merged and every merge is recorded, remove each child worktree with `git worktree remove <absolute_path>` without `--force`, then delete its recorded local branch with `git branch -d <branch>`. Retain and report any worktree or branch that cannot be removed safely. Never remove the integration worktree or any unmerged child branch.
7. Re-inspect dependencies. Before another non-final wave, run a wave check only for cross-child risk not covered by child checks. If `final_check` is next, skip wave validation; never rerun child checks immediately before it.

## Repair waves

- Never continue work on a merged child branch. Group all child-owned findings from one completed review by issue, capture the current integration `HEAD` and issue set, then start one new `issue-<n>-repair-<short-head>` branch in a clean worktree per issue from that HEAD using existing `branch_slug` and `worktree_path` inputs.
- Run each repair group through the frozen-wave contract with Workbench children in parallel.
- If an open implementation wave reports a defect owned by an already-merged predecessor, merge nothing from the open wave. Repair the predecessor in a fresh frozen repair wave, retire the old unmerged worktrees/handoffs without reusing them, and relaunch the entire invalidated wave from the new integration `HEAD` with fresh `branch_slug=retry-<short-head>` branches and worktrees.

## 3. Final check

- Repeat frozen waves while non-final children become runnable. Stop before `final_check` when any non-final child remains blocked, pending, or missing with no independent runnable work.
- Require exactly one `final_check`. After every non-final child is merged, run its named complete integration commands directly on the clean integration branch. It is verification-only: do not launch a child, review it separately, or edit code.
- Route failures to the child owning the failed criterion; ask only when ownership is unclear.
- Record PASS evidence with `manifest.py set-validation --file <event_file>`. Reuse it only when its final issue and `head_sha` match the current `final_check` and `HEAD`.

Default unspecified pytest runs to `uv run pytest -q`; on failure, rerun only the failing slice with diagnostic verbosity. Record known readiness hangs instead of running a predictably blocked broad suite.

## 4. Exact-head review and PR

1. Inspect only structural guards, compact diff statistics, and merge topology.
2. After every child is merged and `final_check` passes, run exactly one parent `$review-checkpoint` with `mode=review_only`, `manifest_path=<absolute manifest>`, and memory skipped. It alone runs the final native subagent review and writes review events.
3. Route findings as `child:<issue>`, `final_check`, `integration`, `stale`, `non_actionable`, or `tooling_unavailable`. Child and final-check defects use a fresh Repair wave; Shipyard fixes only merge conflicts, PR body/progress, or final assembly. After any code fix, rerun final check and this exact-head gate. Do not loop on stale, non-actionable, or unavailable-tool findings.
4. A blocked or unavailable review stops publication. After any review-fix commit, rerun final-check commands and replace the SHA-bound validation event.
5. Invoke nested `$pr-launchpad` with `shipyard_manifest=<absolute manifest>` and memory skipped; Launchpad alone validates manifest reuse at current `HEAD`.

## 5. PR health

1. Take one health snapshot after PR creation and choose exactly one repair owner. Before invoking it, capture `pre_repair_head=$(git rev-parse HEAD)` and the blocker set.
2. For failing GitHub Actions, invoke nested `$ci-repairbay` with an explicit fix request and delegated authority to make scoped commits and push them. For actionable review threads, invoke nested `$review-repairbay` in `clear-all` mode with authority for scoped fixes, commits, pushes, replies, resolutions, and re-fetches. Skip nested memory boundaries and never run both owners concurrently.
3. Trust `status=PASS|BLOCKED|PENDING` unless missing or inconsistent. Return pending work; stop if the same owner returns the same status for the same blocker set at unchanged `HEAD`.
4. Compare current `HEAD` with `pre_repair_head`. Remote-only thread changes leave `HEAD` unchanged: do not rerun code gates; take a fresh snapshot only when remote state changed. If `HEAD` changed, require the repair owner to have committed and pushed it, rerun `final_check`, replace SHA-bound validation, rerun the exact-head `mode=review_only` gate until the manifest accepts PASS, push/confirm that reviewed `HEAD`, then take a fresh snapshot without recreating the PR.
5. Continue one owner at a time until clear. Ignore resolved, outdated, informational, approval, summary, or waived unavailable checks; stop on unchanged repeated blockers, human approval, merge permission, or external-provider blockers.

## Output

Inspect-only returns the parent URL, branch policy, child state/blockers/PR/next action, runnable set, and stop reason. Execution returns the parent and PR URLs, integration branch, manifest path, merged issues, checks, routing, and stop reason. Normal children use one compact line containing issue, head SHA, status, and checks; add branch, worktree, base, or diff details only for blockers or requested diagnostics.
