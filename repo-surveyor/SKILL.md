---
name: repo-surveyor
description: Review a repository without editing code and return evidence-backed maintainability findings. Use for repo scans covering readability, DRY, SOLID, tests, configs, scripts, docs, or architecture.
---

# repo-surveyor

Review only. Do not edit repository source or docs, create patches, rewrite code, commit, or push. Agent-memory may write ignored `.context/` artifacts.

## Memory Boundary

When invoked directly, call `$agent-memory load` before Step 1 and `$agent-memory distill` before every terminal return. A caller that owns the boundary skips both and retains `.context/decisions.jsonl`. Capture only established durable rules, constraints, or reusable root causes—not findings, scores, issue candidates, or routine observations. Memory failure must not replace the survey result or stop reason.

## Scope

Inspect source, tests, config, build scripts, docs, and architecture-relevant files; exclude generated/vendor/third-party files, lockfiles, build outputs, and binaries.

## Workflow

1. Read repo instructions and branch state; inventory eligible files with `rg --files`.
2. Search for repeated patterns and architecture signals. Before each finding, read every file needed for concrete evidence: duplicated logic, unclear boundaries, oversized functions/classes, inconsistent config, weak tests, brittle scripts, or unnecessary abstraction.
3. Classify each finding:
   - Current = the problem is present in the current branch.
   - Solved = the problem appears addressed by current code, docs, or tests; report only to prevent duplicate issue creation.
   - Unclear = evidence is incomplete; label the missing check instead of guessing.
4. For requested issue planning or a full report, dedupe current findings before proposing slices: use `gh issue list --search "<area or exact phrase>" --state open` when available, then `gh issue view <number>` for plausible matches; map each finding to `new`, `duplicate-of #N`, `overlaps #N`, or `solved-by #N`. Do not recommend an issue for duplicate, solved, or cleanup-only findings. Score only new or overlapping current findings:
   - Impact: High = reduces bugs, complexity, onboarding time, or future change risk. Medium = noticeable localized maintainability gain. Low = cleanup or consistency.
   - Effort: Low = less than half a day. Medium = half a day to two days. High = multi-file design work, migration, or careful regression testing.
5. Label assumptions; do not speculate as fact or recommend an abstraction unless it clearly removes duplication or complexity.

## Output

Default output:

1. Lead with the conclusion and highest-value findings.
2. For each, include its `Current`, `Solved`, or `Unclear` classification, path-specific evidence, and smallest credible recommendation.
3. State material assumptions/caveats and the next action. Do not generate issue-planning artifacts unless requested.

When the user requests issue planning or a full report, also include:

- The duplicate matrix and impact/effort for new or overlapping current findings.
- Issue-blueprint handoff JSON using the closest valid shape from `issue-blueprint/references/issue-plan.md`, only for `Current` findings marked `new` or `overlaps #N`.
- Dropped findings with reasons and the remaining work in implementation order.

When the user requests a full report, also include evidence-backed DRY, SOLID, and test-strategy sections; an impact-effort matrix; and a phased roadmap. Include only sections supported by material findings.

Every recommendation must name specific paths, modules, classes, functions, or repeated patterns.
