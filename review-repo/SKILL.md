---
name: review-repo
description: Perform a full-repository maintainability review without editing code. Use when asked to scan a repo and propose evidence-backed improvements for readability, maintainability, DRY, SOLID design, tests, configs, build scripts, docs, or architecture.
---

# review-repo

Review only. Do not edit files, create patches, rewrite code, commit, or push.

## Scope

Inspect source, tests, config, build scripts, docs, and architecture-relevant files. Exclude generated files, vendored dependencies, lockfiles, build outputs, binaries, and third-party code.

## Workflow

1. Read repo instructions and current branch state.
2. Inventory all eligible files with `rg --files`, excluding generated/vendor/build paths.
3. Run repo-wide searches for repeated patterns and architecture signals; read representative files and every file needed to substantiate findings.
4. Search for concrete evidence before each finding: duplicated logic, unclear module boundaries, oversized functions/classes, inconsistent config, weak tests, brittle scripts, or unnecessary abstraction.
5. Score each finding:
   - Impact: High = reduces bugs, complexity, onboarding time, or future change risk. Medium = noticeable localized maintainability gain. Low = cleanup or consistency.
   - Effort: Low = less than half a day. Medium = half a day to two days. High = multi-file design work, migration, or careful regression testing.
6. Label assumptions. Do not speculate as fact. Do not recommend an abstraction unless it clearly removes duplication or complexity.

## Output

Return:

1. Executive summary with the top 3 improvement themes.
2. Impact-Effort Matrix using this table:

| ID | Area | Finding | Recommendation | Impact | Effort | Evidence |
|---|---|---|---|---|---|---|

Group rows under:
- High impact, low effort.
- High impact, high effort.
- Low impact, low effort.
- Low impact, high effort.

Place Medium-scored rows in the closest matching group and keep `Medium` in the table.

3. Top 5 priorities in implementation order.
4. DRY opportunities.
5. SOLID observations.
6. Test strategy improvements.
7. Phased roadmap:
   - Phase 1: quick wins.
   - Phase 2: structural improvements.
   - Phase 3: larger architecture changes.

Every recommendation must name specific paths, modules, classes, functions, or repeated patterns.
