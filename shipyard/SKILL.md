---
name: shipyard
description: Orchestrate a dependency-aware parent issue from its deterministic integration branch into one final PR. Use for issue-blueprint parent issues that need child worktrees, merges, final_check, checks, reviews, and PR routing.
---

# Shipyard

Execute an Issue Blueprint parent graph without duplicating child work. Workbench implements and repairs children; Review Checkpoint owns the review gate; CI and Review Repairbay own PR health; Launchpad creates the PR.

## Inputs and mode

- `parent_issue` is required as a GitHub issue number or URL.
- `--integration-worktree` optionally selects an existing absolute worktree path.
- Infer repository from the GitHub remote, base from the repository default, and the integration branch with `issue-workbench/scripts/branch_name.py integration <parent_issue>`.
- Execute by default. Inspect-only behavior requires an explicit inspect, plan, dry-run, or report request.

Direct invocation owns `$agent-memory load` and distillation before every terminal return. Nested skills skip their memory boundaries and preserve durable candidates for Shipyard; memory failure does not change Shipyard status.

## State and ownership

- The parent issue is durable truth; child bodies define dependencies and PRs define durable implementation progress.
- `.context/shipyard-manifest.json` is the single trusted local run artifact; `manifest.py` alone validates handoffs, lifecycle transitions, validation, and review events. `.context/progress.md` only points to it.
- A child is `done-local` after its recorded branch is merged into the integration branch. Merging the final Shipyard PR makes that completion durable.
- Load each nested skill once, immediately before first use. Query manifest coordination as `issue`, `commit`, `status`, and `verification`; inspect full diffs only for incomplete or surprising evidence or merge conflicts.

## 1. Preflight

1. If provided, require an absolute integration worktree and enter it. Require a clean worktree, fetch remotes, and resolve the default and expected integration branches. Switch to an existing local/remote expected branch; otherwise rename a current non-default branch with no upstream, or create the expected branch from the remote/default base. Never rename the default branch.
2. Run `scripts/inspect_parent_issue.py <parent_issue> --json`. Stop if it cannot resolve the parent, branch policy, graph, `final_check`, or runnable state; report `mode=default_branch_blocked` rather than executing on the default branch.
3. Initialize the manifest before launching children:

   ```bash
   python3 <shipyard_dir>/scripts/manifest.py init <parent_issue> <integration_branch> --base-branch <default_branch>
   ```

Read only issue-linked or named material needed for runnable children.

## 2. Run a frozen wave

1. From the clean integration branch, select the ascending set of current runnable non-final children. Capture that exact set and `wave_base_sha=$(git rev-parse HEAD)`; neither may change before the complete wave is integrated.
2. For each child, require a fresh deterministic sibling worktree path, run `integration_child.py start <issue> --worktree-path <path> --integration-branch <integration_branch>`, and spawn in parallel with `fork_turns=none` using this complete contract:

   ```text
   Use $issue-workbench <child_issue>
   worktree_path=<absolute_child_worktree>
   handoff_mode=integration_branch
   integration_branch=<integration_branch>
   review_base=<integration_branch>
   wait_mode=block
   handoff_path=<absolute_child_worktree>/.context/integration-handoff.json
   ```

   Use `defer` only when explicitly requested. Do not probe running children or delete their worktrees automatically; use absolute paths for mutations once multiple worktrees exist.
3. Ingest every returned handoff through `manifest.py ingest-child --file <path>`. Never reconstruct or separately validate its JSON. Re-append durable child decision records to the Shipyard root through Agent Memory's append helper.
4. Treat the launched set as one barrier. Do not mutate integration `HEAD` or merge any child until every launched handoff has `review:"PASS"` and no `needs_child_fix`. Resume pending reviews after `poll_after_utc`; rerun the owning Workbench child for fixes. Passing siblings remain unmerged.
5. Before the first merge, require current `HEAD` and every retained wave `base_sha` to equal `wave_base_sha`. Stop on drift; never refresh the wave base or children.
6. Merge all PASS branches consecutively in ascending issue order with `integration_child.py merge ... --expected-commit <commit>`, recording each success through `manifest.py merge-child`. Do not validate, re-inspect, reopen diffs, or print detail between merges. Preserve earlier successful merges if a later child conflicts; stop with that child's issue, branch, worktree, and conflicted files.
7. After the batch, run one smallest relevant wave validation and re-inspect dependencies. Reserve the complete integrated suite for `final_check`.

## 3. Final check

- Repeat frozen waves while non-final children become runnable. Stop before `final_check` when any non-final child remains blocked, pending, or missing with no independent runnable work.
- Require exactly one `final_check`. After every non-final child is merged, run its named complete integration commands directly on the clean integration branch. It is verification-only: do not launch a child, review it separately, or edit code.
- Route failures to the child owning the failed criterion; ask only when ownership is unclear.
- Record PASS evidence with `manifest.py set-validation --file <event_file>`. Reuse it only when its final issue and `head_sha` match the current `final_check` and `HEAD`.

Default unspecified pytest runs to `uv run pytest -q`; on failure, rerun only the failing slice with diagnostic verbosity. Record known readiness hangs instead of running a predictably blocked broad suite.

## 4. Exact-head review and PR

1. Inspect only structural guards, compact diff statistics, and merge topology.
2. Run exactly one nested `$review-checkpoint` with `wait_mode=block`, `manifest_path=<absolute manifest>`, and memory skipped. It alone runs Greptile and writes review events.
3. Route findings as `child:<issue>`, `final_check`, `integration`, `stale`, `non_actionable`, or `tooling_unavailable`. Child and final-check defects return to the owning Workbench; ingest repaired PASS handoffs, merge their recorded branches, and rerun relevant checks. Shipyard fixes only merge conflicts, PR body/progress, or final assembly. Do not loop on stale, non-actionable, or unavailable-tool findings.
4. `PENDING_REVIEW` stops publication. After any review-fix commit, rerun final-check commands and replace the SHA-bound validation event.
5. Require manifest reuse at current `HEAD`, then invoke nested `$pr-launchpad` with `shipyard_manifest=<absolute manifest>` and memory skipped:

   ```bash
   python3 <shipyard_dir>/scripts/manifest.py --manifest <manifest_path> can-reuse $(git rev-parse HEAD)
   ```

## 5. PR health

Take one health snapshot after PR creation. Route failing GitHub Actions to nested `$ci-repairbay` and actionable review threads to nested `$review-repairbay`; execution authorizes its scoped fixes, replies, resolutions, and re-fetches unless the user restricted writes. Trust `status=PASS|BLOCKED|PENDING` unless missing or inconsistent, and recheck only after a repair changed state. Ignore resolved, outdated, informational, approval, summary, or waived unavailable checks; stop on human approval, merge permission, or external-provider blockers.

## Output

Inspect-only returns the parent URL, branch policy, child state/blockers/PR/next action, runnable set, and stop reason. Execution returns the parent and PR URLs, integration branch, manifest path, merged issues, checks, routing, and stop reason. Normal children use one compact line containing issue, commit, status, and verification; add branch, worktree, base, or diff details only for blockers or requested diagnostics.
