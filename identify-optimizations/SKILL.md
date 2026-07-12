---
name: identify-optimizations
description: Read a software repository without editing code or running tests, rank its five strongest evidence-backed architecture improvements, and open a concise HTML report with before and after Mermaid diagrams. Use when asked to scan, review, audit, simplify, deepen, or improve a codebase's architecture without implementing changes.
---

# Identify Optimizations

Find up to five changes that concentrate complexity behind smaller interfaces.
Produce the report and stop; do not design or implement them.

## Boundaries

- Treat the repository as read-only: do not edit, create, delete, format, or
  generate repository files, or run tests, builds, linters, formatters, type
  checks, generators, installers, or application commands.
- Use listing, searching, reading files, and version-control status only. The
  temporary HTML report is the sole allowed write.

## Scan

1. Read repository instructions, root README, and manifests; read architecture
   docs, ADRs, and a domain glossary only when present and relevant. Treat them
   as constraints.
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
- `before` and `after` Mermaid diagrams, each with a short `title` and 2–5
  concrete module, interface, service, or state-boundary nodes. Use `flowchart
  TB`, short labels, and evidence-backed dependency arrows.

Use Mermaid only; do not add SVG, canvas, CSS arrows, HTML connectors, or
detailed interfaces.

## Render

Resolve `assets/report.html` relative to this file.

1. Copy it to `${TMPDIR:-/tmp}/architecture-review-<UTC timestamp>.html` (`%TEMP%` on Windows).
2. Replace only the HTML between `REPORT_CONTENT_START` and `REPORT_CONTENT_END`; keep the document shell, CSS, and Mermaid scripts unchanged. Keep all report text in static HTML; JavaScript may only render embedded Mermaid source as SVG.
3. Include one header and one `<article id="candidate-<rank>">` per candidate.
   Put each required `Before` and `After` diagram in `.visual.before` and
   `.visual.after` with one `<pre class="mermaid">` each, followed by `Problem`
   and `Proposal`. Escape repository-derived HTML; keep labels and prose short.
4. Confirm one article and two Mermaid blocks per candidate, exact repo-relative evidence paths, static visible report text, and the absolute output path. The unchanged template owns the Mermaid script and document shell.
5. Return the absolute report path. Stop there.
