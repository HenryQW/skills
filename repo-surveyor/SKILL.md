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
6. When the user requests issue planning or a full report, dedupe current findings against existing tracker issues before proposing issue slices:
   - List likely matching open issues with `gh issue list --search "<area or exact phrase>" --state open` when GitHub is available.
   - View plausible matches with `gh issue view <number>` before declaring a new issue.
   - Produce a duplicate matrix that maps each finding to `new`, `duplicate-of #N`, `overlaps #N`, or `solved-by #N`.
   - Do not create or recommend an issue for duplicate, solved, or cleanup-only findings.
7. When the user requests issue planning or a full report, score each current finding. For issue slices, retain only new or overlapping findings:
   - Impact: High = reduces bugs, complexity, onboarding time, or future change risk. Medium = noticeable localized maintainability gain. Low = cleanup or consistency.
   - Effort: Low = less than half a day. Medium = half a day to two days. High = multi-file design work, migration, or careful regression testing.
8. Label assumptions. Do not speculate as fact. Do not recommend an abstraction unless it clearly removes duplication or complexity.

## Output

Default output:

1. Lead with the conclusion and the highest-value findings.
2. For each finding, include its `Current`, `Solved`, or `Unclear` classification, exact path-specific evidence, and the smallest credible recommendation.
3. State material assumptions or caveats.
4. End with the next action. Do not generate issue-planning artifacts unless requested.

When the user requests issue planning or a full report, also include:

- A duplicate matrix mapping each finding to `new`, `duplicate-of #N`, `overlaps #N`, or `solved-by #N`.
- Impact and effort for new or overlapping current findings.
- Issue-blueprint handoff JSON using the closest valid shape from `issue-blueprint/references/issue-plan.md`. Include only `Current` findings whose duplicate decision is `new` or `overlaps #N`.
- Dropped findings with reasons and the remaining work in implementation order.

When the user requests a full report, also include evidence-backed DRY, SOLID, and test-strategy sections; an impact-effort matrix; and a phased roadmap. Include only sections supported by material findings.

Every recommendation must name specific paths, modules, classes, functions, or repeated patterns.
