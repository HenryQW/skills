---
name: repo-surveyor
description: Review a repository without editing code and return evidence-backed maintainability findings. Use for repo scans covering readability, DRY, SOLID, tests, configs, scripts, docs, or architecture.
---

# repo-surveyor

Review only. Do not edit repository source or docs, create patches, rewrite code, commit, or push. Agent-memory may write ignored `.context/` artifacts.

## Memory Boundary

- When the user invokes `repo-surveyor` directly, call `$agent-memory load` before Step 1 and `$agent-memory distill` as the final guard before every terminal return.
- When a caller owns the memory boundary, skip both calls and preserve `.context/decisions.jsonl` for that caller.
- Capture only an established durable repository rule, architectural constraint, or reusable root cause. Do not capture audit findings, scores, issue candidates, or routine observations.
- Memory failure must not replace the survey result or stop reason.

## Scope

Inspect source, tests, config, build scripts, docs, and architecture-relevant files. Exclude generated files, vendored dependencies, lockfiles, build outputs, binaries, and third-party code.

## Workflow

1. Read repo instructions and current branch state.
2. Inventory all eligible files with `rg --files`, excluding generated/vendor/build paths.
3. Run repo-wide searches for repeated patterns and architecture signals; read representative files and every file needed to substantiate findings.
4. Search for concrete evidence before each finding: duplicated logic, unclear module boundaries, oversized functions/classes, inconsistent config, weak tests, brittle scripts, or unnecessary abstraction.
5. Classify each finding:
   - Current = the problem is present in the current branch.
   - Solved = the problem appears addressed by current code, docs, or tests; report only to prevent duplicate issue creation.
   - Unclear = evidence is incomplete; label the missing check instead of guessing.
6. Dedupe current findings against existing tracker issues before proposing issue slices:
   - List likely matching open issues with `gh issue list --search "<area or exact phrase>" --state open` when GitHub is available.
   - View plausible matches with `gh issue view <number>` before declaring a new issue.
   - Produce a duplicate matrix that maps each finding to `new`, `duplicate-of #N`, `overlaps #N`, or `solved-by #N`.
   - Do not create or recommend an issue for duplicate, solved, or cleanup-only findings.
7. Score each new or overlapping current finding:
   - Impact: High = reduces bugs, complexity, onboarding time, or future change risk. Medium = noticeable localized maintainability gain. Low = cleanup or consistency.
   - Effort: Low = less than half a day. Medium = half a day to two days. High = multi-file design work, migration, or careful regression testing.
8. Label assumptions. Do not speculate as fact. Do not recommend an abstraction unless it clearly removes duplication or complexity.

## Output

Default to the compact output unless the user asks for a full maintainability report.

Compact output:

1. Executive summary with the top 3 improvement themes.
2. Current vs solved classification:

| ID | Area | Classification | Evidence | Notes |
|---|---|---|---|---|

3. Duplicate matrix:

| ID | Proposed issue slice | Existing issue check | Decision | Reason |
|---|---|---|---|---|

4. Impact-Effort Matrix using this table:

| ID | Area | Finding | Recommendation | Impact | Effort | Evidence |
|---|---|---|---|---|---|---|

Group rows under:
- High impact, low effort.
- High impact, high effort.
- Low impact, low effort.
- Low impact, high effort.

Place Medium-scored rows in the closest matching group and keep `Medium` in the table.

5. Issue-blueprint handoff JSON for the remaining new work, using the closest valid shape from `issue-blueprint/references/issue-plan.md`. Include only findings whose duplicate-matrix decision is `new` or `overlaps #N` and whose current-vs-solved classification is `Current`.
6. Dropped findings list with reason, including duplicate, solved, unclear, and cleanup-only items.
7. Top 5 priorities in implementation order.
8. Brief DRY opportunities.
9. Brief SOLID observations.
10. Brief test strategy improvements.
11. Brief phased roadmap: quick wins, structural improvements, larger architecture changes.

For a full maintainability report, expand items 8-11 with supporting evidence and phase details.

Every recommendation must name specific paths, modules, classes, functions, or repeated patterns.
