---
name: repo-surveyor
description: Review a repository without editing code or running tests, then open an HTML report with ranked, evidence-backed maintainability findings and before-and-after Mermaid diagrams. Use when asked to scan, review, audit, simplify, optimize, or improve a codebase's architecture without implementing changes.
---

# repo-surveyor

Review only. Do not edit repository source or docs, create patches, rewrite code, commit, push, or run tests, builds, linters, formatters, type checks, generators, installers, or application commands. Agent-memory may write ignored `.context/` artifacts; the temporary HTML report is the only other allowed write.

## Memory Boundary

When invoked directly, call `$agent-memory load` before Step 1 and `$agent-memory distill` before every terminal return. A caller that owns the boundary skips both and retains `.context/decisions.jsonl`. Capture only established durable rules, constraints, or reusable root causes—not findings, scores, issue candidates, or routine observations. Memory failure must not replace the survey result or stop reason.

## Survey

1. Read repository instructions, branch state, root README, and manifests. Read relevant architecture docs, ADRs, and domain glossary when present; treat them as constraints. Inventory eligible files with `rg --files`, excluding generated, vendor, third-party, dependency, build, cache, binary, and lock files. Respect dirty worktree changes.
2. Make one breadth pass over source, tests, config, scripts, docs, entry points, major modules, dependency direction, state ownership, and test seams. Explicitly assess:
   - DRY: duplicated policy, orchestration, validation, config, or domain logic—not incidental syntax.
   - SOLID: concrete responsibility, extension, substitutability, interface, or dependency-direction friction; do not score principles mechanically.
   - Test strategy: behavior coverage, test seams, brittleness, and important untested risk.
   - Architecture: module depth, boundaries, locality, state ownership, dependency leakage, and unnecessary abstraction.
3. Use focused reads to prove candidates. Read every file needed for exact evidence, but do not read every file or delegate by default. Prefer changes that concentrate complexity behind smaller interfaces. Reject style-only, speculative, cleanup-only, or ADR-conflicting ideas unless current friction justifies reopening the decision.
4. Classify evidence as `Current`, `Solved`, or `Unclear`. For `Unclear`, name the missing check instead of guessing. Stop after the main hotspots are sampled and up to five current candidates have survived verification.
5. Label assumptions. Do not recommend an abstraction unless it clearly removes duplication or complexity.

Use repository domain terms. Use `module`, `interface`, `implementation`, `depth`, `seam`, `adapter`, `leverage`, and `locality` consistently when they clarify the evidence.

## Rank

Rank current candidates by user impact, architectural leverage, confidence, and change size. Do not pad the list or force a priority level.

- `P0`: active correctness, security, or data-integrity risk only.
- `P1`: high-leverage maintainability problem.
- `P2`: worthwhile improvement with lower urgency.

Each candidate requires:

- `rank`, `title`, `priority`, and `Current` classification;
- exact repo-relative `files` and 1–3 concrete `evidence` items;
- a one-sentence `problem` and smallest credible `proposal`;
- up to three concrete `benefits`;
- `before` and `after` Mermaid diagrams, each with a short title and 2–5 concrete module, interface, service, or state-boundary nodes. Use `flowchart TB`, short labels, and evidence-backed dependency arrows.

Use Mermaid only; do not add SVG, canvas, CSS arrows, HTML connectors, or detailed interfaces.

## Issue-planning Handoff

Hard boundary: a default invocation stops after opening the report. Do not call or hand off to issue-blueprint, dedupe issues, or create planning artifacts unless the user explicitly requested issue planning when invoking repo-surveyor.

When issue planning was explicitly requested, dedupe current findings with `gh issue list --search "<area or exact phrase>" --state open` when available, then inspect plausible matches with `gh issue view <number>`. Map each candidate to `new`, `duplicate-of #N`, `overlaps #N`, or `solved-by #N`; do not propose issues for duplicate, solved, or cleanup-only findings.

For `new` and `overlaps #N` candidates, include impact (`High`, `Medium`, or `Low`), effort (`Low`, `Medium`, or `High`), and issue-blueprint handoff JSON using the closest valid shape in `issue-blueprint/references/issue-plan.md`. Include the duplicate matrix, dropped findings with reasons, and remaining work in implementation order.

## Render

Resolve `assets/report.html` relative to this file. Every survey produces and opens an HTML report; do not substitute a chat-only review.

1. Copy the template to `${TMPDIR:-/tmp}/repository-survey-<UTC timestamp>.html` (`%TEMP%` on Windows).
2. Replace only the HTML between `REPORT_CONTENT_START` and `REPORT_CONTENT_END`. Keep the document shell, CSS, and Mermaid scripts unchanged. Escape repository-derived HTML; all report text must remain static HTML, and JavaScript may only render embedded Mermaid source.
3. Include a header, concise conclusion, and explicit evidence-backed DRY, SOLID, test-strategy, and architecture coverage sections, including when a category has no material finding.
4. Add one `<article id="candidate-<rank>">` per ranked candidate. Include its classification, priority, files, evidence, benefits, problem, proposal, and required diagrams in `.visual.before` and `.visual.after`, each containing one `<pre class="mermaid">`.
5. If no current candidate survives, do not invent one. Instead include one unranked architecture overview with paired Mermaid diagrams showing the observed structure and the unchanged recommended structure, clearly stating that no structural change is recommended from sampled evidence.
6. When issue planning was requested, add its duplicate matrix, impact/effort, handoff JSON, dropped findings, and implementation order to the static report.
7. Confirm the required coverage sections, exact evidence paths, one paired Mermaid comparison per candidate, static visible text, and absolute output path. Open the report with the platform's local file opener and return the absolute path plus material caveats.
