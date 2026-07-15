---
name: repo-surveyor
description: Review a repository without editing code or running tests, then open an HTML report with ranked, evidence-backed maintainability findings and before-and-after Mermaid diagrams. Use when asked to scan, review, audit, simplify, optimize, or improve a codebase's architecture without implementing changes.
---

# repo-surveyor

Review only. Do not edit the repository or run tests, builds, linters,
formatters, type checks, generators, installers, or application commands. The
temporary HTML report is the only write besides ignored agent-memory artifacts.

## Memory

Direct invocation owns `$agent-memory`; nested invocation defers it to the
caller. Capture only established durable rules, constraints, or reusable root
causes—not findings, scores, issue candidates, or routine observations.

## Survey

1. Read repository instructions, branch state, README, manifests, and relevant
   architecture decisions or domain terms. Inventory with `rg --files`, excluding
   generated, vendor, dependency, build, cache, binary, and lock files; preserve
   and account for dirty user changes.
2. Make one breadth pass over source, tests, config, scripts, entry points,
   boundaries, dependencies, state ownership, and test seams. Explicitly assess
   DRY, SOLID, test strategy, and architecture without mechanical scoring.
3. Prove candidates with focused reads. Reject style-only, speculative,
   cleanup-only, or decision-conflicting ideas; label evidence `Current`,
   `Solved`, or `Unclear` and name the missing check for `Unclear`.
4. Stop after the main hotspots and at most five verified `Current` candidates.
   Rank by impact, architectural leverage, confidence, and change size; use
   `P0` only for active correctness, security, or data-integrity risk, `P1` for
   high-leverage maintainability, and `P2` for worthwhile lower urgency.

Each ranked candidate needs rank, title, priority, `Current` classification,
exact files, 1–3 evidence items, a one-sentence problem and smallest credible
proposal, up to three benefits, and paired
`flowchart TB` Mermaid diagrams titled before/after with 2–5 evidence-backed
module, interface, service, or state-boundary nodes. Do not force findings or
recommend abstractions without demonstrated complexity reduction.

## Optional Issue Planning

Default invocation stops after the report. Only an issue-planning request made
when invoking this skill permits issue deduplication and an `issue-blueprint`
handoff. Query plausible open issues with `gh`; classify candidates as `new`,
`duplicate-of #N`, `overlaps #N`, or `solved-by #N`. Hand off the existing
report path, ranked evidence-backed candidates, duplicate classifications,
dropped reasons, and material constraints. Do not construct issue-plan JSON or
a new planning artifact: Issue Blueprint alone owns issue slicing,
dependencies, validation, graph JSON, approval, and publication.

## Report

Copy `assets/report.html` to
`${TMPDIR:-/tmp}/repository-survey-<UTC timestamp>.html`. Replace only content
between `REPORT_CONTENT_START` and `REPORT_CONTENT_END`; escape repository text
and keep JavaScript limited to Mermaid rendering. Include a header, conclusion,
explicit DRY/SOLID/test-strategy/architecture coverage, and one
`<article id="candidate-<rank>">` per finding with the required evidence and
`.visual.before`/`.visual.after` Mermaid blocks. With no finding, render one
unranked paired overview showing no recommended structural change. Include
optional planning output only when authorized. Verify visible static text,
paths, diagrams, and the absolute output path; open the report and return its
path plus material caveats.
