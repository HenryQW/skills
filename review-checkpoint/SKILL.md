---
name: review-checkpoint
description: Run blocker-only branch reviews through a native read-only reviewer subagent. Direct review requests are read-only; explicit fix loops and coordinating workflows may apply deterministic in-scope fixes.
---

# Review Checkpoint

Use one native read-only reviewer subagent as the branch-diff gate. Review is read-only unless `fix_loop` is explicitly authorized or selected by a coordinating workflow.

## Inputs

- `mode`: `review_only` (direct default) or `fix_loop` (explicit fix/coordinator default).
- `max_iterations`: default `3`.
- `review_base`: optional caller-provided base ref.
- `manifest_path`: optional and only for Shipyard's integration review; child reviews keep isolated state in their handoffs.

## Memory

Direct invocation owns `$agent-memory`; nested Workbench or Shipyard invocation
defers it to the caller. Capture only accepted durable review rules or reusable
root causes.

## Findings and authorization

- Classify findings as `spec_blocker` (acceptance or unrequested behavior), `standards_blocker` (repository rules), `safety_blocker` (data, secrets, security, or forbidden paths), `test_blocker` (missing or misleading validation), or `non_actionable`.
- A blocker is actionable only when deterministic, in scope, and fixable without a product decision. Cosmetic, speculative, stale, broad, unclear, contradictory, or out-of-scope findings are `non_actionable`.
- `review_only` never edits. `fix_loop` fixes only actionable findings and each iteration must reduce that set. Do not loop on non-actionable findings.
- Stop when the budget is spent, a finding repeats after its targeted fix, or a later finding contradicts an accepted one. Record contradictions as `non_actionable: contradictory semantics`.

## Review loop

1. Require a clean worktree except local `.context/progress.md` and a named local branch. Resolve `review_base`, `base_sha`, and `head_sha`; the reviewed branch does not need an upstream.
2. For the current `(base_sha, head_sha)`, spawn exactly one native read-only reviewer subagent with `fork_turns=none`, choosing the least-cost sufficient reviewer role under repository instructions. Do not use an external review service or substitute a local self-review.
3. Give the reviewer the absolute worktree, branch, base and head SHAs, reproducible diff refs, task requirements, repository instructions, and validation evidence. Require it to inspect the actual diff and relevant callers/tests, make no edits or state changes, and return only `PASS` or blocker findings with taxonomy, file/line evidence, impact, and the smallest credible fix.
4. Validate each finding against scope and current `HEAD`; reclassify unsupported findings as `non_actionable`.
5. The final gate is the latest completed subagent review with no later commit. If no reviewer subagent is available or it fails without a result, return `BLOCKED` with the tooling failure.

Append compact review history to `.context/review-events.jsonl`; do not create per-review folders.

## Complete or fix

- No actionable blocker -> `PASS`.
- Actionable blockers in `review_only` -> `BLOCKED` with findings and no edits.
- In `fix_loop`, apply the smallest fix, inspect the diff, run the smallest relevant check, commit inspected files, and return to Step 1 for the new `HEAD`.

When `manifest_path` is set, record pass, blocker, or tooling-failure events through:

```bash
python3 <shipyard_dir>/scripts/manifest.py --manifest <manifest_path> set-review --file <event_file>
```

A passing integration event must contain `status:"PASS"`, current `branch`, `base_sha`, and exact reviewed `head_sha`; return `PASS` only after the manifest accepts it.

## Output

Return `PASS` or `BLOCKED` with mode, reviewer role, reviewed base/head SHAs, checks, and unresolved actionable blockers.
