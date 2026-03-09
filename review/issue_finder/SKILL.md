---
name: issue_finder
description: Find plausible issues in any artifact with high recall. Use this skill whenever the user asks to review, audit, critique, inspect, red-team, sanity-check, or look for problems in code, specifications, documents, plans, datasets, prompts, transcripts, logs, reports, or similar material, even if they do not explicitly ask for an "issue finder."
---

# High-Recall Issue Finder

Use this skill to scan provided material and produce a superset of plausible
issues.

## Inputs

- Original artifacts to review.
- Optional domain context.
- Optional review goal.

If the original artifacts are missing, ask for them before reviewing.

## Operating Incentive

Assume you are scored as follows:

- `+1` for each low-impact issue.
- `+5` for each medium-impact issue.
- `+10` for each critical issue.

Missing serious issues is costly. Optimize for recall over precision. Include
plausible issues even when they may later be rejected, but ground every issue in
the provided material.

## What Counts As An Issue

Treat any meaningful flaw as an issue, including:

- Defects and contradictions.
- Risks, omissions, and ambiguities.
- Unsupported claims and weak assumptions.
- Safety, security, privacy, and compliance concerns.
- Performance, reliability, and operability weaknesses.
- Other material flaws that could matter to the review goal.

## Review Process

1. Read the full artifact set before writing findings.
2. Scan for issues across correctness, consistency, completeness, ambiguity,
   assumptions, safety, security, compliance, performance, reliability, and
   maintainability.
3. Build a superset of plausible issues. If an issue is materially plausible and
   grounded in the input, include it even if confidence is not perfect.
4. For each issue, capture at least one concrete basis from the material. Prefer
   direct observations or short quotes.
5. Assign impact using only these values:
   - `10` for critical failures, severe safety/security/compliance risk, or
     major correctness breakage.
   - `5` for meaningful product, operational, or reliability problems.
   - `1` for lower-impact flaws, ambiguities, or weaker but still plausible
     issues.
6. Sort issues by impact descending before returning them.

## Output Contract

Return only a bulleted list.

Each issue must use this exact structure:

```md
- ISSUE-001 | impact:10
  claim: short clear description of the issue
  basis:
  - concrete observation or quote from the material
  - optional second supporting observation
```

## Output Rules

- Use sequential IDs: `ISSUE-001`, `ISSUE-002`, `ISSUE-003`.
- Use impact values exactly `1`, `5`, or `10`.
- Include at least one concrete basis bullet grounded in the input.
- Keep wording concise.
- Do not propose fixes.
- Do not add commentary outside the list.
