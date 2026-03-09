---
name: issue_review_pipeline
description: Run the full three-stage issue review workflow by invoking issue_finder, issue_adversary, and issue_referee in sequence. Use this skill whenever the main agent wants the end-to-end review pipeline run automatically over provided artifacts, with optional domain context, review goals, or constraints.
---

# Issue Review Pipeline

Use this skill only as an orchestrator for these downstream skills:

1. `issue_finder`
2. `issue_adversary`
3. `issue_referee`

Do not perform substantive review, analysis, judgment, fixing, or issue
adjudication yourself.

## Inputs

- original artifacts
- optional domain context
- optional review goal
- optional constraints

If the original artifacts are missing, ask for them before starting.

## Handoff Rules

- Preserve the original artifact order across all stages.
- Preserve every `ISSUE-###` identifier exactly as emitted by `issue_finder`.
- Pass prior-stage outputs verbatim to the next stage.
- Do not rewrite, renumber, merge, split, reorder, reinterpret, summarize, or
  filter any issue between stages.
- Do not add commentary outside the required stage inputs and final output.

## Workflow

### Stage 1

Invoke `issue_finder` with:

- original artifacts
- optional domain context
- optional review goal
- optional constraints

Collect the full output exactly as returned.

### Stage 2

Invoke `issue_adversary` with:

- original artifacts
- the full output of `issue_finder`
- any optional domain context still relevant
- any optional review goal still relevant
- any optional constraints still relevant

Collect the full output exactly as returned.

### Stage 3

Invoke `issue_referee` with:

- original artifacts
- the full output of `issue_finder`
- the full output of `issue_adversary`
- any optional domain context still relevant
- any optional review goal still relevant
- any optional constraints still relevant

Collect the full output exactly as returned.

## Downstream Failure Handling

If any downstream skill is unavailable, fails during execution, or returns
malformed output, stop immediately.

Treat output as malformed only when the downstream skill fails its own required
output contract or the handoff integrity rules above.

Do not continue to later stages after a failure.
Do not repair, replace, simulate, approximate, or complete a failed stage.

Return only this exact error format:

```md
Error: <stage_name> failed due to <unavailability|malformed output|execution failure>.
```

## Final Output

On success, return only the full output of `issue_referee` exactly as returned.

## Hard Prohibitions

- Never perform substantive review work.
- Never add issues.
- Never remove issues.
- Never challenge issues.
- Never adjudicate issues.
- Never propose fixes.
- Never substitute your own reasoning for any downstream skill.
- Never add any text before or after the final `issue_referee` bullet list.
