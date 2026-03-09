---
name: trueflow_adversary
description: Attack `trueflow_initializer` findings using the original artifacts and persist the review to `.context/trueflow/adversary.md`. Use this skill whenever the main agent has both the original artifacts and the output table from `trueflow_initializer` and needs to challenge, rebut, or pressure-test candidate findings in any generic evaluation workflow, even when the task is not issue-focused.
---

# Trueflow Adversary

Use this skill as an adversarial reviewer against claims from
`trueflow_initializer`.

Optimize for correct challenges against the original artifacts. Attack each
claim aggressively, but only when the original artifacts actually defeat or
materially weaken it.

## Workspace

- Use `.context/trueflow/` as the durable workspace.
- Write the stage output to `.context/trueflow/adversary.md`.
- Read the initializer handoff from `.context/trueflow/initializer.md` when the
  caller provides that file path or asks you to use the workspace artifact.

## Required Inputs

Require both of the following inputs:

- original artifacts
- the full table contents from `trueflow_initializer`

If either input is missing, ask for the missing material. Do not attempt to
challenge findings from summaries alone when the original artifacts are
unavailable.

## Canonical Claim Set

Treat the rows from `trueflow_initializer` as the authoritative set of claims.

Produce exactly one review row for each initializer row.

Preserve every `Index` and `Context / Topic` value exactly as written in
`trueflow_initializer`.

Preserve every `FINDING-###` identifier exactly as written inside
`Initializer Finding`.

Preserve the original row order.

## Operating Incentive

Assume you are scored per claim as follows:

- If you correctly challenge a weak or false finding, gain its importance
  score.
- If you incorrectly challenge a real finding, lose `2x` its importance score.

Attempt to challenge findings aggressively, but only when the evidence in the
original artifacts actually defeats or materially undercuts them.

## Adversarial Review Process

For each row:

1. Read the relevant original artifacts directly.
2. Identify the exact allegation in `Initializer Finding`.
3. Look for direct counter-evidence, limiting conditions, or reasoning errors in
   the finding.
4. Use `challenged` only when the original artifacts defeat or materially
   weaken the finding.
5. Use `not challenged` when the finding survives review.

Judge the claim against the original artifacts, not against speculation.

Do not invent missing constraints, missing evidence, or hypothetical
counterexamples.

Do not challenge a finding only because it is weakly phrased. Challenge it only
when the underlying allegation is defeated or materially weakened by the
material.

## Output Contract

Write `.context/trueflow/adversary.md` as a Markdown table with this exact
header:

```md
| Index | Context / Topic | Initializer Finding | Adversary Finding | Referee Verdict |
|---|---|---|---|---|
```

Row rules:

- Fill only `Index`, `Context / Topic`, and `Adversary Finding`.
- Leave `Initializer Finding` and `Referee Verdict` blank.
- Preserve `Index` and `Context / Topic` exactly from `trueflow_initializer`.
- `Adversary Finding` must use this exact single-line format:
  `FINDING-001; challenged; basis: <grounded counter-evidence>`
  or
  `FINDING-001; not challenged; basis: <grounded reason>`
- Keep every table cell on a single line.
- Do not propose fixes.

After writing the file, return only this exact path:

```text
.context/trueflow/adversary.md
```

## Output Rules

- Produce exactly one row for each initializer row.
- Preserve the finding ID exactly.
- Include at least one grounded basis in every `Adversary Finding` cell.
- Do not add commentary before or after the table in the file.
- Do not return the table inline in chat.
