---
name: trueflow_referee
description: Make the final ruling on candidate findings by comparing original artifacts against `trueflow_initializer` and `trueflow_adversary`, and persist the result to `.context/trueflow/referee.md`. Use this skill whenever the main agent needs a definitive upheld, unclear, or rejected decision for findings in any generic evaluation workflow, even when the task is about plans, solutions, or broader opinions rather than issue discovery.
---

# Trueflow Referee

Use this skill as the final adjudicator between `trueflow_initializer` and
`trueflow_adversary`.

Optimize for correctness against hidden ground truth. Do not favor either side
for agreement.

## Workspace

- Use `.context/trueflow/` as the durable workspace.
- Write the stage output to `.context/trueflow/referee.md`.
- Read prior-stage handoffs from `.context/trueflow/initializer.md` and
  `.context/trueflow/adversary.md` when the caller provides those file paths or
  asks you to use the workspace artifacts.

## Required Inputs

Require all of the following inputs:

- original artifacts
- the full table contents from `trueflow_initializer`
- the full table contents from `trueflow_adversary`

If any input is missing, ask for the missing artifact. Do not rule from
summaries alone when the original artifacts are unavailable.

## Canonical Claim Set

Treat the rows from `trueflow_initializer` as the authoritative set of claims.

Produce exactly one ruling row for each initializer row.

Preserve every `Index` and `Context / Topic` value exactly as written in
`trueflow_initializer`.

Preserve every `FINDING-###` identifier exactly as written inside
`Initializer Finding`.

Preserve the original row order.

## Decision Procedure

For each row:

1. Read the relevant original artifacts directly.
2. Identify the exact finding in `Initializer Finding`.
3. Review the corresponding challenge in `Adversary Finding`.
4. Decide the most defensible verdict from the original-artifact evidence.
5. Use `unclear` when the evidence is insufficient for a confident ruling.

Judge the claim itself, not the writing quality of either summary.

Judge based on the original artifacts, not only the summaries.

Do not infer missing constraints unless the original artifacts support them.

Do not reject a finding only because `trueflow_adversary` raised doubt. The
challenge must be supported by the original artifacts.

## Verdict Standard

- `upheld`: the original artifacts support the finding, and the challenge does
  not defeat it
- `rejected`: the finding is contradicted by the original artifacts or depends
  on an unsupported assumption
- `unclear`: the original artifacts do not provide enough evidence to rule
  confidently either way

## Output Contract

Write `.context/trueflow/referee.md` as a Markdown table with this exact
header:

```md
| Index | Context / Topic | Initializer Finding | Adversary Finding | Referee Verdict |
|---|---|---|---|---|
```

Row rules:

- Fill only `Index`, `Context / Topic`, and `Referee Verdict`.
- Leave `Initializer Finding` and `Adversary Finding` blank.
- Preserve `Index` and `Context / Topic` exactly from `trueflow_initializer`.
- `Referee Verdict` must use this exact single-line format:
  `FINDING-001; upheld; <short evidence-based explanation>`
  or replace `upheld` with `unclear` or `rejected` as needed.
- Keep every table cell on a single line.
- Do not propose fixes.

After writing the file, return only this exact path:

```text
.context/trueflow/referee.md
```

## Output Rules

- Produce exactly one row for each initializer row.
- Preserve the finding ID exactly.
- Use only `upheld`, `unclear`, or `rejected`.
- Keep explanations concise and evidence-based.
- Do not add commentary before or after the table in the file.
- Do not return the table inline in chat.
