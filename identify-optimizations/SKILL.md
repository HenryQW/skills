---
name: identify-optimizations
description: Read a software repository without editing code or running tests, rank its five strongest evidence-backed architecture improvements, and open a concise HTML report with before and after Mermaid diagrams. Use when asked to scan, review, audit, simplify, deepen, or improve a codebase's architecture without implementing changes.
---

# Identify Optimizations

Find five changes that concentrate complexity behind smaller interfaces. Produce the report and stop; do not design or implement the changes.

## Boundaries

- Treat the repository as read-only. Do not edit, create, delete, format, or generate repository files.
- Do not run tests, builds, linters, formatters, type checks, generators, installers, or application commands.
- Use only read-only inspection such as listing, searching, reading files, and checking version-control status. The temporary HTML report is the only allowed write.

## Scan

1. Read repository instructions, the root README, manifests, architecture docs, ADRs, and any domain glossary. Treat them as constraints, not suggestions.
2. Exclude generated, vendored, build, cache, and dependency directories. Respect dirty worktree changes.
3. Run one breadth pass over entry points, major modules, dependency direction, state ownership, and test seams, then use focused reads to prove candidates. Do not read every file or delegate by default. Stop when five candidates have concrete evidence and the main hotspots have been sampled.
4. Look for:
   - shallow modules whose interface nearly matches their implementation;
   - policy or state ownership scattered across files;
   - dependency details leaking across a seam;
   - repeated orchestration that belongs in one module;
   - code that is hard to test through its real interface.
5. Apply the deletion test: prefer a candidate when removing the current seam would concentrate complexity instead of merely moving it.
6. Verify each candidate with exact files and concrete code evidence. Reject style-only, speculative, or ADR-conflicting ideas unless current friction justifies reopening the decision.

Use `module`, `interface`, `implementation`, `depth`, `seam`, `adapter`, `leverage`, and `locality` consistently. Use domain terms from the repository.

## Rank

Rank by user impact, architectural leverage, confidence, and change size. Select the strongest five; do not pad the list if fewer than five survive verification. Assign urgency as `P0` (address first), `P1` (next), or `P2` (later).

Each candidate needs:

- `rank`, `title`, and `priority`: `P0`, `P1`, or `P2`;
- involved `files` and 1–3 short `evidence` items;
- one-sentence `problem` and `proposal`;
- up to three concrete `benefits`;
- `before` and `after` Mermaid architecture diagrams, each with a short `title` and 2–5 concrete module, interface, service, or state-boundary nodes. Use `flowchart TB`, short node labels, and only evidence-backed dependency arrows.

Do not propose detailed interfaces.

## Render

Resolve `assets/report.html` relative to this file.

1. Copy it to `${TMPDIR:-/tmp}/architecture-review-<UTC timestamp>.html` (`%TEMP%` on Windows).
2. Replace only the HTML between `REPORT_CONTENT_START` and `REPORT_CONTENT_END`; keep the document shell, CSS, and Mermaid scripts unchanged. Keep all report text in static HTML; JavaScript may only render embedded Mermaid source as SVG.
3. Include one header and one `<article id="candidate-<rank>">` per candidate. Each article must show labeled `Before` and `After` diagrams using `.visual.before` and `.visual.after`, with one `<pre class="mermaid">flowchart TB ...</pre>` in each, followed by `Problem` and `Proposal`. Escape repository-derived HTML and keep Mermaid labels short. Keep prose terse; the diagrams and evidence should carry the report.
4. Confirm the candidate count, ten Mermaid diagrams, the pinned `https://cdn.jsdelivr.net/npm/mermaid@11.16.0/dist/mermaid.min.js` script, absence of other external scripts, exact repo-relative evidence paths, static visible report text, and absolute output path. Open the report with `open`, `xdg-open`, or `start`.
5. Return the absolute report path. Stop there.
