---
name: skill-optimizer
description: Optimize existing skills by finding evidence-backed failures and waste, calibrating triggers, instructions, resources, and safety, applying the smallest root-cause change, and verifying representative behavior. Use when asked to improve, streamline, harden, reduce turn, tool, or context waste in, or optimize an existing skill; do not use for creating a brand-new skill.
---

# skill-optimizer

Improve an existing skill from observed behavior. If none exists, use
`$skill-creator`.

## Inputs

`target_skill_path` is required unless unambiguous. `optimization_goal` defaults
to evidenced waste and correctness problems while preserving outcomes and public
contracts. `mode` is read-only `diagnose` or explicitly authorized `apply`.
Prefer supplied prompts, traces, outputs, failures, or feedback; derive only a
small representative set when absent.

## Workflow

1. Read repository instructions, target metadata and entrypoint, then only
   referenced code, resources, tests, or callers needed to prove behavior.
2. Establish positive, non-trigger, and regression cases. Baseline relevant
   outcomes, turns, tool calls, repeated context, noise, recovery, and safety;
   use concrete static evidence when execution is unsafe or unavailable.
3. Rank only evidenced selection, instruction, context, execution, recovery,
   authorization, or verification problems by impact, confidence, and fix size.
4. In `diagnose`, report evidence, impact, and the smallest credible fix without
   mutation. In `apply`, delete duplication first, then patch the smallest causal
   owner. Prefer existing mechanisms; add a helper only for deterministic
   reliability or a repeated fragile sequence. Do not add compatibility layers
   unless a public contract requires them.
5. Preview only to reduce material uncertainty. Explicit edits authorize scoped
   local changes, not irreversible, externally visible, destructive, or expanded
   actions. Dry-run and apply must be exclusive, and helpers must not bypass
   wrapper safety.
6. Verify changed behavior with the smallest structural and representative
   positive/negative/regression checks, compare to baseline, and update required
   repository inventory or install documentation.

Report only what improved, passed, and remains.
