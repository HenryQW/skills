---
name: trueflow
description: Run the full generic trueflow pipeline by invoking `trueflow_initializer`, `trueflow_adversary`, and `trueflow_referee` in sequence, persisting stage outputs under `.context/trueflow/`, and returning a consolidated `findings.md` table. Use this skill whenever the user asks to "use trueflow" or wants multiple agents to review artifacts, solution proposals, coding implementation plans, documents, prompts, or other material and return adjudicated findings rather than a single opinion.
---

# Trueflow

Use this skill only as an orchestrator for these downstream skills:

1. `trueflow_initializer`
2. `trueflow_adversary`
3. `trueflow_referee`

Do not perform substantive evaluation, analysis, judgment, or fixing yourself.

## Workspace

- Use `.context/trueflow/` as the durable workspace.
- Stage outputs:
  - `.context/trueflow/initializer.md`
  - `.context/trueflow/adversary.md`
  - `.context/trueflow/referee.md`
- Consolidated output:
  - `.context/trueflow/findings.md`

## Inputs

- original artifacts
- optional domain context
- optional evaluation goal
- optional constraints

If the original artifacts are missing, ask for them before starting.

## Handoff Rules

- Preserve the original artifact order across all stages.
- Use `.context/trueflow/initializer.md` as the canonical row scaffold.
- Preserve every `Index`, `Context / Topic`, and `FINDING-###` identifier
  exactly as emitted by `trueflow_initializer`.
- Pass prior-stage outputs verbatim to the next stage.
- Do not rewrite, renumber, merge, split, reorder, reinterpret, summarize, or
  filter any row between stages.
- Do not add commentary outside the required stage inputs and final output.

## Workflow

### Stage 1

Invoke `trueflow_initializer` with:

- original artifacts
- optional domain context
- optional evaluation goal
- optional constraints

Require the downstream response to be exactly:

```text
.context/trueflow/initializer.md
```

Then read the full contents of `.context/trueflow/initializer.md`.

### Stage 2

Invoke `trueflow_adversary` with:

- original artifacts
- the full contents of `.context/trueflow/initializer.md`
- any optional domain context still relevant
- any optional evaluation goal still relevant
- any optional constraints still relevant

Require the downstream response to be exactly:

```text
.context/trueflow/adversary.md
```

Then read the full contents of `.context/trueflow/adversary.md`.

### Stage 3

Invoke `trueflow_referee` with:

- original artifacts
- the full contents of `.context/trueflow/initializer.md`
- the full contents of `.context/trueflow/adversary.md`
- any optional domain context still relevant
- any optional evaluation goal still relevant
- any optional constraints still relevant

Require the downstream response to be exactly:

```text
.context/trueflow/referee.md
```

Then read the full contents of `.context/trueflow/referee.md`.

## Consolidation

After all three stages succeed, write `.context/trueflow/findings.md` as a
Markdown table with this exact header:

```md
| Index | Context / Topic | Initializer Finding | Adversary Finding | Referee Verdict |
|---|---|---|---|---|
```

Consolidation rules:

- Use the rows from `.context/trueflow/initializer.md` as the authoritative row
  order.
- Copy `Index`, `Context / Topic`, and `Initializer Finding` from
  `.context/trueflow/initializer.md`.
- Copy `Adversary Finding` from `.context/trueflow/adversary.md`.
- Copy `Referee Verdict` from `.context/trueflow/referee.md`.
- Do not rewrite any copied cell text.
- Fail if any row count, row order, `Index`, `Context / Topic`, or
  `FINDING-###` identifier is inconsistent across files.

## Downstream Failure Handling

If any downstream skill is unavailable, fails during execution, or returns
malformed output, stop immediately.

Treat output as malformed when any of the following occurs:

- the downstream response is not the exact expected path
- the expected file is missing
- the file does not contain the required table header
- row counts differ across stage files
- any row changes `Index`, `Context / Topic`, or `FINDING-###` unexpectedly
- a stage file fills columns other than its own stage column

Do not continue to later stages after a failure.
Do not repair, replace, simulate, approximate, or complete a failed stage.

Return only this exact error format:

```md
Error: <stage_name> failed due to <unavailability|malformed output|execution failure>.
```

Use `stage_name` values `trueflow_initializer`, `trueflow_adversary`,
`trueflow_referee`, or `trueflow_consolidation`.

## Final Output

On success, return only the full contents of `.context/trueflow/findings.md`
exactly as written.

## Hard Prohibitions

- Never perform substantive evaluation work.
- Never add findings.
- Never remove findings.
- Never challenge findings.
- Never adjudicate findings.
- Never propose fixes.
- Never substitute your own reasoning for any downstream skill.
- Never rewrite stage cell contents during consolidation.
- Never add any text before or after the final consolidated table.
