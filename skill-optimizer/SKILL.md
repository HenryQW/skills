---
name: skill-optimizer
description: Optimize existing skills by finding evidence-backed failures and waste, calibrating triggers, instructions, resources, and safety, applying the smallest root-cause change, and verifying representative behavior. Use when asked to improve, streamline, harden, reduce turn, tool, or context waste in, or optimize an existing skill; do not use for creating a brand-new skill.
---

# skill-optimizer

Improve an existing skill from observed behavior, not from a generic checklist.
If no target skill exists yet, stop and use `$skill-creator`.

## Inputs

- `target_skill_path` is required unless the named skill is unambiguous. `optimization_goal` defaults to removing evidenced waste and correctness problems while preserving outcomes and public contracts. `mode` is `diagnose` for read-only analysis or `apply` only when edits were requested. Prefer supplied real `evidence` (prompts, traces, outputs, failures, or feedback); derive a small representative set only when absent.

## Rules

- Read repository instructions, target metadata/`SKILL.md`, and only needed references, scripts, assets, tests, callers, or helpers. Keep diagnostics read-only; resolve from the request, evidence, and safe defaults, asking only when choices materially change scope, risk, or behavior.
- Patch the smallest causal surface: prefer deletion and existing mechanisms over new prose, files, helpers, or compatibility layers. Preserve internal names/signatures only when public contracts require it.
- Keep final output to what improved, passed, and remains.

## Establish Behavior

1. Define positive, negative/non-trigger, and regression cases: intent/authorization routing, intended outcomes, and unchanged behavior.
2. Map only applicable selection (metadata, overlaps, handoffs), instruction (hard domain/safety/authorization/success constraints, defaults, stops, and output versus inferable procedure), context (footprint, nesting, loading), execution (entrypoints, side effects, recovery), and verification (checks and sync) surfaces.
3. Before editing, observe representative cases when feasible and record a baseline of outcomes, turns, tool calls, repeated reads, noise, fragile steps, and context at start and with nesting. If execution is unsafe or unavailable, use and state concrete static evidence.

## Find Problems

Look for:

- selection/metadata failures, contradictory or duplicated instructions, missing defaults, and inappropriate specificity
- eager or duplicated context, deep/undiscoverable references, repeated discovery, unclear handoffs, noisy output, or brittle commands
- unsafe authorization or confirmation, mutating dry-runs, non-idempotent applies, recovery gaps, or weak/duplicated validation

Rank findings by observed impact, confidence, and fix size. Do not optimize speculative problems.

## Contracts

For `diagnose`:

Perform one bounded discovery pass, expanding only for evidence-backed controlling dependencies. Report each material finding with evidence, impact, and the smallest credible fix. Do not mutate the target or its environment.

For `apply`:

Treat an explicit edit request as authorization for ordinary scoped changes. Preview when it reduces material uncertainty; request authorization for actions not already authorized, especially irreversible, externally visible, or out of scope—preview grants none. Apply the smallest cohesive root-cause fix, read back applicable side effects, and run only required post-actions.

When the target exposes dry-run and apply modes, dry-run must not mutate, the modes must be mutually exclusive, and helper arguments must not bypass wrapper safety.

## Patch

Delete stale or duplicate material first; otherwise fix the existing metadata, `SKILL.md`, reference, asset, script, helper, guard, runner, or audit that owns the behavior. Add a helper only for deterministic reliability or a repeated fragile sequence. Move detail to a new file only when conditional loading materially reduces context or isolates a real variant.

## Verify

Run the smallest checks that cover the changed behavior:

- structural validation/metadata consistency and focused checks for changed scripts or execution paths
- positive, negative, and regression cases for changed selection/instructions; clean-context forward tests when substantial or generalization-sensitive
- before/after comparison against the baseline and preserved behavior, plus required repository inventory, audit, install, or adversarial review

Structural validation is necessary but not sufficient. Update root inventory, metadata, and install instructions whenever the repository requires it.
