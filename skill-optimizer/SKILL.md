---
name: skill-optimizer
description: Optimize existing skills by finding evidence-backed failures and waste, calibrating triggers, instructions, resources, and safety, applying the smallest root-cause change, and verifying representative behavior. Use when asked to improve, streamline, harden, reduce turn, tool, or context waste in, or optimize an existing skill; do not use for creating a brand-new skill.
---

# skill-optimizer

Improve an existing skill from observed behavior, not from a generic checklist.
If no target skill exists yet, stop and use `$skill-creator`.

## Inputs

- `target_skill_path`: required unless the user names a skill that can be found unambiguously.
- `optimization_goal`: optional; default to removing evidenced waste and correctness problems while preserving intended outcomes and public contracts.
- `mode`: optional; use `diagnose` for read-only analysis and `apply` only when the user asked for edits.
- `evidence`: optional prompts, traces, outputs, failures, or user feedback; prefer real evidence and derive a small representative set only when none exists.

## Rules

- Read repository instructions, target metadata and `SKILL.md`, and only the references, scripts, assets, tests, callers, or transitive helpers needed to follow the behavior being optimized.
- Keep read-only diagnostics separate from mutating workflows.
- Resolve choices from the user's request, repository evidence, and safe defaults. Ask only when plausible choices materially change scope, risk, or intended behavior.
- Patch the smallest causal surface. Prefer deletion and existing mechanisms over new prose, files, helpers, or compatibility layers.
- Do not preserve old internal helper names, variables, or signatures unless a public contract requires it.
- Keep final output compact: what improved, what passed, and what remains.

## Establish Behavior

1. Define representative positive cases, negative or non-trigger cases, intended outcomes, and behavior that must remain unchanged.
2. Classify the skill as workflow, tool-integration, knowledge or domain, artifact-producing, or hybrid.
3. Map only the applicable surfaces:
   - selection: frontmatter description, UI metadata, overlaps, and handoffs
   - instruction: defaults, decisions, degrees of freedom, stop conditions, and output contract
   - context: references, progressive disclosure, duplicated guidance, and resource loading
   - execution: entrypoints, scripts, state, side effects, recovery, and post-actions
   - verification: validators, tests, smoke checks, forward tests, and repository sync
4. Before editing, observe representative cases when feasible and record a baseline: wrong outcomes, repeated decisions, unnecessary turns or tool calls, repeated reads, noisy output, or fragile manual steps. If execution is unsafe or unavailable, use concrete static artifact evidence and state that limitation.

## Find Problems

Look for:

- under-triggering, over-triggering, conflicting skills, or stale metadata
- contradictions, duplicated instructions, missing defaults, or specificity that does not match task fragility
- eager context loading, deep reference chains, duplicated reference content, or undiscoverable resources
- repeated discovery, unclear handoffs, rewritten deterministic work, noisy output, or brittle command sequences
- unnecessary confirmation, unsafe authorization assumptions, dry-run mutations, non-idempotent apply paths, partial-failure gaps, or missing recovery
- structural validation without representative behavior checks, contaminated forward tests, stale tests, or duplicated verification

Rank findings by observed impact, confidence, and fix size. Do not optimize speculative problems.

## Contracts

For `diagnose`:

1. Perform one bounded discovery pass and expand only when evidence identifies a controlling dependency.
2. Report each material finding with evidence, impact, and the smallest credible fix.
3. Do not mutate the target or its environment.

For `apply`:

1. Treat an explicit user request to edit as authorization for ordinary scoped repository changes.
2. Preview when it reduces material uncertainty. Request explicit authorization when an action is not already clearly authorized, especially if it is irreversible, externally visible, or outside the established scope; preview does not grant authorization.
3. Apply the smallest cohesive root-cause fix.
4. Read back side effects when applicable, and reuse that readback as final verification when it proves the outcome.
5. Run post-actions only when the selected path or repository requires them.

When the target exposes dry-run and apply modes, dry-run must not mutate, the modes must be mutually exclusive, and helper arguments must not bypass wrapper safety.

## Patch

Choose the fix from the cause:

1. Delete stale or duplicated instructions, resources, or steps.
2. Fix metadata or `SKILL.md` when selection, defaults, or decisions are wrong.
3. Fix an existing reference, asset, script, helper, guard, runner, or audit when it owns the behavior.
4. Add a helper only when deterministic reliability is needed or the same fragile sequence is repeated.

Avoid moving detail into a new file unless conditional loading will materially reduce context or isolate a real variant.

## Verify

Run the smallest checks that cover the changed behavior:

- structural validation and metadata consistency for changed skill folders
- focused tests or smoke checks for changed scripts and execution paths
- representative positive, negative, and regression cases for changed selection or instructions
- clean-context forward tests for substantial or generalization-sensitive changes
- before and after comparison against the baseline and preserved behavior
- repository-required inventory, audit, install, or adversarial-review checks

Structural validation is necessary but not sufficient. Update root inventory, metadata, and install instructions whenever the repository requires it.
