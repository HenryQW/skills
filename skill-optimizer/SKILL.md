---
name: skill-optimizer
description: Optimize existing Codex workflow skills by tracing the active skill flow, removing repeated decisions, tightening dry-run/apply safety, compacting docs, and updating the smallest shared surface. Use when Codex is asked to improve, streamline, harden, reduce turn waste in, or optimize an existing skill; do not use for creating a brand-new skill.
---

# skill-optimizer

Optimize an existing skill by removing repeated decisions, not by hiding decisions.
If no target skill exists yet, stop and use `$skill-creator`.

## Inputs

- `target_skill_path`: required unless the user names a skill that can be found unambiguously.
- `optimization_goal`: optional; default to reducing workflow waste without changing user-facing behavior.
- `mode`: optional; use `diagnose` for read-only analysis and `apply` only when the user asked for edits.

## Rules

- Read only the target `SKILL.md`, route manifests, primary references, directly called scripts, and local tests/audits needed for verification.
- Keep read-only diagnostics separate from mutating workflows.
- Do not infer ambiguous domain, route, event, helper, or lifecycle choices. Require explicit input.
- Patch the smallest shared surface: manifest, dispatch helper, guard, runner, or audit before per-skill prose.
- Do not add compatibility for old internal helper names, variables, or signatures unless a public CLI contract requires it.
- Keep final output compact: what changed, what passed, what remains.

## Map Flow

1. Identify public entrypoints: user invocation text, CLI commands, helper scripts, route manifests, and post-actions.
2. Identify safety controls: dry-run/apply flags, confirmation guards, write boundaries, and readback checks.
3. Identify verification: tests, audits, smoke commands, review gates, and README or metadata sync.
4. Classify each path:
   - read-only diagnostic
   - preview-only workflow
   - mutating workflow
   - post-sync or post-apply action

## Find Waste

Look for:

- repeated route discovery
- unclear handoffs between skills
- helpers that print too much
- dry-run/apply inconsistencies
- missing confirmation guards
- stale docs/tests causing false investigations
- duplicated verification across chained actions
- scripts whose output forces agents to re-parse noisy logs

## Contracts

For read-only diagnostics:

1. One discovery step.
2. One diagnostic command or focused inspection.
3. Compact findings with evidence.
4. No write path.

For mutating workflows:

1. One route lookup.
2. One preview.
3. Explicit confirmation before apply.
4. One narrow apply.
5. One readback.
6. One final verification.
7. Post-sync actions only when the selected route requires them.
8. Compact final output.

Dry-run must reject apply flags. Apply must require explicit confirmation. Helper arguments must not bypass wrapper safety.

## Patch

Prefer these fixes, in order:

1. Route manifest or dispatch helper.
2. Shared confirmation or mode guard.
3. One wrapper or runner for repeated command sequences.
4. Audit or test fix for known false positives.
5. Short `SKILL.md` edits that point agents to the optimized path.

Avoid new helper scripts until the same command sequence is repeated across multiple skills or is too fragile for prose.

## Verify

Run the smallest checks that cover changed behavior:

- skill validation for changed skill folders
- route or manifest audit when routes changed
- stale workflow audit when docs or handoffs changed
- focused tests for helper behavior
- smoke test for the optimized command path
- adversarial review when the repo workflow requires it

Update the root skill inventory, metadata, or install instructions whenever the repository requires that for changed skills.
