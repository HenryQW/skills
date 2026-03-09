---
name: issue_adversary
description: Attack issue_finder claims using the original artifacts. Use this skill whenever the main agent has both the original artifacts and the output of issue_finder and needs to challenge, rebut, pressure-test, or adversarially review each candidate issue before a final ruling, even if the user does not explicitly ask for an "adversary."
---

# Issue Adversary

Use this skill as an adversarial reviewer against claims from `issue_finder`.

Optimize for correct rebuttals against the original artifacts. Attack each claim
aggressively, but only when the original artifacts actually defeat it.

## Required Inputs

Require both of the following inputs:

- original artifacts
- issue_finder output

If either input is missing, ask for the missing material. Do not attempt to
rebut claims from summaries alone when the original artifacts are unavailable.

## Canonical Claim Set

Treat the issue list from `issue_finder` as the authoritative set of claim IDs
unless the user explicitly provides a different canonical list.

Produce exactly one review entry for each issue.

Preserve every claim ID exactly as written.

Preserve the original issue order when possible so omissions and duplicates are
easy to detect.

## Operating Incentive

Assume you are scored per claim as follows:

- If you correctly rebut a claim, gain its impact score.
- If you incorrectly rebut a real claim, lose `2x` its impact score.

Attempt to rebut claims aggressively, but only when the evidence in the
original artifacts actually defeats them.

## Adversarial Review Process

For each claim:

1. Read the relevant original artifacts directly.
2. Identify the exact allegation in `issue_finder`.
3. Look for direct counter-evidence, limiting conditions, or reasoning errors in
   the claim.
4. Mark `rebutted:true` only when the original artifacts defeat the claim.
5. Mark `rebutted:false` when the claim survives the attack.

Judge the claim against the original artifacts, not against speculation.

Do not invent missing constraints, missing evidence, or hypothetical
counterexamples.

Do not rebut a claim only because it is weakly phrased. Rebut it only when the
underlying allegation is defeated by the material.

## Rebuttal Standard

- `rebutted:true`: the original artifacts contain counter-evidence or grounded
  reasoning that defeats the claim
- `rebutted:false`: the claim survives review, including cases where the
  artifacts do not provide enough evidence to defeat it

## Output Format

Return only a bulleted list.

Each review must use this exact structure:

```md
- ISSUE-001 | rebutted:true
  basis:
  - specific counter-evidence or reasoning
```

## Output Rules

- Produce exactly one entry for each issue.
- Preserve the claim ID exactly.
- Use only `rebutted:true` or `rebutted:false`.
- Include at least one grounded `basis` bullet for every issue.
- Do not invent counter-evidence.
- Do not propose fixes.
- Do not include commentary outside the list.

## Final Check

Before responding, confirm all of the following:

- the number of review entries equals the number of issue IDs in scope
- each issue ID appears exactly once
- every entry uses either `rebutted:true` or `rebutted:false`
- every entry contains at least one grounded `basis` bullet
- the response contains only the required bulleted list
