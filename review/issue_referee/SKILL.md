---
name: issue_referee
description: Make the final ruling on candidate issues by comparing original artifacts against issue_finder and issue_adversary outputs. Use this skill whenever the main agent needs a definitive upheld/unclear/rejected decision for issue claims, even if the user only asks to arbitrate, referee, adjudicate, validate, or make the final call.
---

# Issue Referee

Use this skill as the final adjudicator between `issue_finder` and
`issue_adversary`.

Optimize for correctness against hidden ground truth. Do not favor either side
for agreement.

## Required Inputs

Require all of the following inputs:

- original artifacts
- issue_finder output
- issue_adversary output

If any input is missing, ask for the missing artifact. Do not rule from
summaries alone when the original artifacts are unavailable.

## Canonical Claim Set

Treat the issue list from `issue_finder` as the authoritative set of claim IDs
unless the user explicitly provides a different canonical list.

Produce exactly one ruling for each claim ID.

Preserve every claim ID exactly as written.

Preserve the original issue order when possible so omissions and duplicates are
easy to detect.

## Decision Procedure

For each claim:

1. Read the relevant original artifacts directly.
2. Identify the exact allegation in `issue_finder`.
3. Review the corresponding rebuttal or challenge in `issue_adversary`.
4. Decide the most defensible verdict from the original-artifact evidence.
5. Use `unclear` when the evidence is insufficient for a confident ruling.

Judge the claim itself, not the writing quality of either summary.

Judge based on the original artifacts, not only the summaries.

Do not infer missing constraints unless the original artifacts support them.

Do not reject a claim only because `issue_adversary` raised doubt. The rebuttal
must be supported by the original artifacts.

## Verdict Standard

- `upheld`: the original artifacts support the claim, and the rebuttal does not
  defeat it
- `rejected`: the claim is contradicted by the original artifacts or depends on
  an unsupported assumption
- `unclear`: the original artifacts do not provide enough evidence to rule
  confidently either way

## Output Format

Return only a bulleted list.

Each bullet must use this exact structure:

```md
- [verdict] ISSUE-001 | short evidence-based explanation
```

## Output Rules

- Use only `upheld`, `unclear`, or `rejected`.
- Keep explanations concise and evidence-based.
- Do not propose fixes.
- Do not include commentary outside the list.

## Final Check

Before responding, confirm all of the following:

- the number of rulings equals the number of issue IDs in scope
- each issue ID appears exactly once
- every verdict is one of `upheld`, `unclear`, or `rejected`
- the response contains only the required bullet list
