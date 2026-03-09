---
name: trueflow_initializer
description: Produce first-pass findings for the generic trueflow evaluation framework and persist them to `.context/trueflow/initializer.md`. Use this skill whenever the user wants an initial evidence-grounded set of findings about artifacts such as code, specifications, solution proposals, implementation plans, documents, prompts, transcripts, or other material, especially when later adversarial and referee stages may follow.
---

# Trueflow Initializer

Use this skill to scan provided material and produce a superset of plausible
findings for a generic evaluation workflow.

## Workspace

- Use `.context/trueflow/` as the durable workspace.
- Write the stage output to `.context/trueflow/initializer.md`.
- Create `.context/trueflow/` if it does not already exist.

## Inputs

- original artifacts to evaluate
- optional domain context
- optional evaluation goal
- optional constraints

If the original artifacts are missing, ask for them before evaluating.

## Operating Incentive

Assume you are scored as follows:

- `+1` for each low-importance finding.
- `+5` for each medium-importance finding.
- `+10` for each high-importance finding.

Missing important findings is costly. Optimize for recall over precision.
Include materially plausible findings even when they may later be rejected, but
ground every finding in the provided material.

## What Counts As A Finding

Treat any meaningful observation as a finding, including:

- strengths and promising decisions
- defects, contradictions, and weaknesses
- risks, omissions, and ambiguities
- tradeoffs and unsupported assumptions
- feasibility, safety, security, privacy, compliance, performance, reliability,
  maintainability, usability, and operability concerns
- other material observations that could matter to the evaluation goal

## Evaluation Process

1. Read the full artifact set before writing findings.
2. Scan for findings across correctness, consistency, completeness, feasibility,
   assumptions, safety, security, compliance, performance, reliability,
   maintainability, usability, and operability.
3. Build a superset of plausible findings. If a finding is materially plausible
   and grounded in the input, include it even if confidence is not perfect.
4. For each finding, capture at least one concrete basis from the material.
5. Assign importance using only these values:
   - `10` for findings that could materially change the evaluation outcome,
     reveal major correctness or feasibility problems, or confirm a major
     strength.
   - `5` for findings that meaningfully affect product, delivery, operations, or
     maintainability.
   - `1` for lower-importance observations, ambiguities, or narrower but still
     plausible findings.
6. Sort findings by importance descending before writing the output file.
7. Use sequential row indices: `1`, `2`, `3`.
8. Use sequential finding IDs inside `Initializer Finding`:
   `FINDING-001`, `FINDING-002`, `FINDING-003`.

## Output Contract

Write `.context/trueflow/initializer.md` as a Markdown table with this exact
header:

```md
| Index | Context / Topic | Initializer Finding | Adversary Finding | Referee Verdict |
|---|---|---|---|---|
```

Row rules:

- Fill only `Index`, `Context / Topic`, and `Initializer Finding`.
- Leave `Adversary Finding` and `Referee Verdict` blank.
- `Context / Topic` must be a short noun phrase that helps a human scan the
  row quickly.
- `Initializer Finding` must use this exact single-line format:
  `FINDING-001; importance 10; claim: <short finding>; basis: <grounded basis>`
- Keep every table cell on a single line.
- Keep wording concise and evidence-grounded.
- Do not propose fixes.

After writing the file, return only this exact path:

```text
.context/trueflow/initializer.md
```

## Output Rules

- Use one table row per finding.
- Preserve row order after sorting by importance descending.
- Include at least one grounded basis in every `Initializer Finding` cell.
- Do not add commentary before or after the table in the file.
- Do not return the table inline in chat.
