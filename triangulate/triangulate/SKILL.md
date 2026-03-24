---
name: triangulate
description: Evaluate supplied artifacts and return a consolidated findings table with evidence-based conclusions. Use this skill when the user wants a proposal, plan, code change, document, prompt, transcript, or other material reviewed through a structured multi-perspective evaluation instead of a single opinion.
---

# Triangulate

Use this skill to evaluate supplied artifacts and return a consolidated findings
table with evidence-based conclusions.

Handle the full review flow end to end. Own validation, persistence, and
final rendering, and keep user-facing responses focused on the review outcome
rather than implementation details.

## Workspace

Use `.context/triangulate/` as the durable workspace.

Persist only canonical JSON stage artifacts plus the final human-facing report:

- `.context/triangulate/initializer.json`
- `.context/triangulate/normalized.json`
- `.context/triangulate/adversary.json`
- `.context/triangulate/referee.json`
- `.context/triangulate/findings.md`

Create `.context/triangulate/` if it does not already exist.

Do not persist stage markdown files.

## Inputs

- original artifacts
- optional domain context
- optional evaluation goal
- optional constraints

If the original artifacts are missing, ask for them before starting.

## Canonical Row Schema

Use JSON for all internal handoffs. Every subagent output must use the same
canonical top-level shape:

```json
{
  "rows": []
}
```

The meaning of fields depends on stage, but row identity always uses:

- `index`
- `context_topic`
- `finding_id`

All evidence-bearing fields must be single-line strings and must include
specific evidence references.

An evidence reference must identify where the support came from, such as file
path, section name, heading, paragraph, or line range.

Examples:

- `spec/auth.md lines 41-57`
- `README section "Failure handling"`
- `api/openapi.yaml path /sessions/{id}`

## Stage Schemas

### Initializer JSON

```json
{
  "rows": [
    {
      "index": 1,
      "context_topic": "<short noun phrase>",
      "finding_id": "FINDING-001",
      "importance": 10,
      "claim": "<short finding>",
      "basis": "<grounded basis>",
      "evidence_refs": [
        "<specific evidence reference>"
      ]
    }
  ]
}
```

### Normalizer JSON

```json
{
  "rows": [
    {
      "index": 1,
      "context_topic": "<normalized short noun phrase>",
      "finding_id": "FINDING-001",
      "importance": 10,
      "claim": "<normalized short finding>",
      "basis": "<grounded basis retained or tightened>",
      "evidence_refs": [
        "<specific evidence reference>"
      ]
    }
  ]
}
```

### Adversary JSON

```json
{
  "rows": [
    {
      "index": 1,
      "context_topic": "<must exactly match normalized output>",
      "finding_id": "FINDING-001",
      "status": "challenged",
      "basis": "<grounded counter-evidence or grounded survival reason>",
      "evidence_refs": [
        "<specific evidence reference>"
      ]
    }
  ]
}
```

`status` may be only `challenged` or `not challenged`.

### Referee JSON

```json
{
  "rows": [
    {
      "index": 1,
      "context_topic": "<must exactly match normalized output>",
      "finding_id": "FINDING-001",
      "verdict": "upheld",
      "explanation": "<short evidence-based explanation>",
      "evidence_refs": [
        "<specific evidence reference>"
      ]
    }
  ]
}
```

`verdict` may be only `upheld`, `unclear`, or `rejected`.

## Validation Rules

The top-level orchestrator must validate all of the following.

### Initializer validation

- output is valid JSON
- top-level object contains `rows`
- `rows` is a non-empty array
- every row contains `index`, `context_topic`, `finding_id`, `importance`,
  `claim`, `basis`, and `evidence_refs`
- `index` values are sequential integers starting at `1`
- `finding_id` values are sequential in the form `FINDING-001`, `FINDING-002`,
  `FINDING-003`
- `importance` values are only `10`, `5`, or `1`
- `context_topic`, `claim`, and `basis` are non-empty single-line strings
- `evidence_refs` is a non-empty array of non-empty single-line strings
- rows are sorted by `importance` descending
- `finding_id` values are unique

### Normalizer validation

- output is valid JSON
- top-level object contains `rows`
- `rows` is a non-empty array
- every row contains `index`, `context_topic`, `finding_id`, `importance`,
  `claim`, `basis`, and `evidence_refs`
- duplicate or overlapping initializer findings may be merged, split, removed,
  or rewritten only when the result is more canonical, non-redundant, and
  evidence-grounded
- `index` values are sequential integers starting at `1`
- `finding_id` values are sequential in the form `FINDING-001`, `FINDING-002`,
  `FINDING-003`
- `importance` values are only `10`, `5`, or `1`
- `context_topic`, `claim`, and `basis` are non-empty single-line strings
- `evidence_refs` is a non-empty array of non-empty single-line strings
- rows are sorted by `importance` descending
- `finding_id` values are unique

### Adversary validation

- output is valid JSON
- row count exactly matches normalized row count
- every row contains `index`, `context_topic`, `finding_id`, `status`, `basis`,
  and `evidence_refs`
- `index`, `context_topic`, and `finding_id` exactly match normalized output
  row-for-row
- `status` is only `challenged` or `not challenged`
- `basis` is a non-empty single-line string
- `evidence_refs` is a non-empty array of non-empty single-line strings
- no duplicate `finding_id`

### Referee validation

- output is valid JSON
- row count exactly matches normalized row count
- every row contains `index`, `context_topic`, `finding_id`, `verdict`,
  `explanation`, and `evidence_refs`
- `index`, `context_topic`, and `finding_id` exactly match normalized output
  row-for-row
- `verdict` is only `upheld`, `unclear`, or `rejected`
- `explanation` is a non-empty single-line string
- `evidence_refs` is a non-empty array of non-empty single-line strings
- no duplicate `finding_id`

## Review Process

### Pass 1: generate candidate findings

Invoke the `initializer` subagent using the prompt file at
`../subagents/initializer.md` with:

- original artifacts
- optional domain context
- optional evaluation goal
- optional constraints

Require JSON output matching the initializer schema.

Validate it.

Persist the raw validated JSON to `.context/triangulate/initializer.json`.

### Pass 2: normalize the claim set

Invoke the `normalizer` subagent using the prompt file at
`../subagents/normalizer.md` with:

- original artifacts
- the validated initializer JSON
- optional domain context still relevant
- optional evaluation goal still relevant
- optional constraints still relevant

Require JSON output matching the normalizer schema.

Validate it.

Persist the raw validated JSON to `.context/triangulate/normalized.json`.

### Pass 3: challenge the normalized claims

Invoke the `adversary` subagent using the prompt file at
`../subagents/adversary.md` with:

- original artifacts
- the validated normalized JSON
- optional domain context still relevant
- optional evaluation goal still relevant
- optional constraints still relevant

Require JSON output matching the adversary schema.

Validate it against normalized output.

Persist the raw validated JSON to `.context/triangulate/adversary.json`.

### Pass 4: adjudicate the final conclusions

Invoke the `referee` subagent using the prompt file at
`../subagents/referee.md` with:

- original artifacts
- the validated normalized JSON
- the validated adversary JSON
- optional domain context still relevant
- optional evaluation goal still relevant
- optional constraints still relevant

Require JSON output matching the referee schema.

Validate it against normalized output.

Persist the raw validated JSON to `.context/triangulate/referee.json`.

## Consolidation

After all four stages succeed, write `.context/triangulate/findings.md` as a
Markdown table with this exact header:

```md
| Index | Context / Topic | Normalized Finding | Adversary Finding | Referee Verdict |
|---|---|---|---|---|
```

Use normalized rows as the authoritative row order.

For each row, render exactly:

- `Index` from normalized output
- `Context / Topic` from normalized output
- `Normalized Finding` as:
  `FINDING-001; importance 10; claim: <claim>; basis: <basis>; refs: <ref1>, <ref2>`
- `Adversary Finding` as:
  `FINDING-001; challenged; basis: <basis>; refs: <ref1>, <ref2>`
  or:
  `FINDING-001; not challenged; basis: <basis>; refs: <ref1>, <ref2>`
- `Referee Verdict` as:
  `FINDING-001; upheld; <explanation>; refs: <ref1>, <ref2>`
  or replace `upheld` with `unclear` or `rejected` as needed

Do not rewrite any copied cell text during consolidation except to render the
required final string formats from validated JSON.

## Failure Handling

If any subagent is unavailable, returns malformed JSON, fails validation, or
fails during execution, stop immediately.

Do not continue to later stages after a failure.

Do not repair, replace, simulate, approximate, or complete a failed stage.

Return only this exact error format:

```md
Error: <stage_name> failed due to <unavailability|malformed output|execution failure>.
```

Use `stage_name` values `initializer`, `normalizer`, `adversary`, `referee`, or
`consolidation`.

## Final Output

On success, return only the full contents of `.context/triangulate/findings.md`
exactly as written.

## Hard Prohibitions

- Never perform substantive evaluation work in the top-level orchestrator.
- Never normalize findings in the top-level orchestrator.
- Never add findings in the top-level orchestrator.
- Never remove findings in the top-level orchestrator.
- Never challenge findings in the top-level orchestrator.
- Never adjudicate findings in the top-level orchestrator.
- Never propose fixes in the top-level orchestrator.
- Never substitute your own reasoning for subagent outputs.
- Never persist stage markdown files.
- Never add any text before or after the final consolidated table.
