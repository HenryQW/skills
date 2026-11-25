---
name: living-docs
description: Keep a project's specs, design docs, slice briefs and owner decisions current while it is built in slices. Use when you plan a multi-slice project, write or update a slice brief, record an owner decision, change a spec or design doc, archive an outdated doc, or write a walkthrough or handoff.
---

# Living Docs

A doc is current, or it is in `archive/`. Every change that makes a doc wrong fixes that doc in the same commit.

## Scope

- This skill owns the doc set of a project and the rules that keep it current.
- Record each chosen term, its meaning, and rejected alternatives in the glossary. Use the `domain-modeling` skill when available. Record a hard-to-reverse choice in an architecture decision record (ADR).
- Repository rules (`AGENTS.md`, an existing layout) win. Map this layout onto the files that exist:
  - An existing `GLOSSARY.md` or `CONTEXT.md` is the names doc. Do not add `names.md` beside it.
  - An existing `docs/adr/` stays the home of hard-to-reverse decisions. The decision log entry links to the ADR.
- Keep code-dependent docs beside their code. In a monorepo, each package or app has its own `docs/`.

## Layout

```text
docs/
  README.md          index: Doc | Holds | Read when, plus the rules in this skill
  overview.md        what it is, goals, parts, build order
  names.md           Name | Means | Not
  decisions.md       owner decisions, newest last
  slices/README.md   # | Slice | Brief | State, rows in build order
  slices/NN-name.md  one brief per slice
  archive/README.md  what the archive is and which files briefs still read
```

- For a normative contract, write one `spec.md` and start it with "This document is normative."
- For a library with many rules, write one `design.md` as the single current statement of every rule. Fold each decision into it in the same commit. The decision log keeps the history and the reason.
- Create a file only when it has content.

## Rules

1. **Current or archived.** When a change alters a name, a part or a decision, update every doc that states it in the same commit. Move a doc that no longer describes the plan or the code to `archive/`.
2. **One name per thing.** Add a name to the names doc before you use it. The `Not` column lists rejected names. A rename changes every current doc in the same commit; the archive keeps old names.
3. **One owner per fact.** Link to the owner. Do not copy text between docs.
4. **Precedence.** Decisions and slice briefs win over the archive. The current spec or design doc states the rule; the decision log states why.
5. **Indexes are complete.** `docs/README.md` and `slices/README.md` list every file in their folder.

## Decision log

Append one bullet per decision, newest last:

```markdown
- **Short title (owner, YYYY-MM-DD: "exact words of the owner"):** The rule. The reason.
```

- Record the decision when the owner makes it. Do not batch.
- Quote the owner's exact words. If you have no exact words, write `(owner, YYYY-MM-DD)` without a quote.
- Never delete or rewrite an entry. Supersede it:
  - Prefix the old entry with `**(Superseded by "New title", YYYY-MM-DD.)**`.
  - Start the new entry's rule with `Supersedes "Old title".`
- Cite a decision elsewhere as decision "Short title".
- A change to the slice order is a decision.
- A default that the agent takes goes in the slice brief under `Decided`, marked *default*. It enters the log only when the owner confirms it.

## Asking the owner

- Stop only the work that depends on the decision. Continue other work.
- Ask one decision at a time: the problem, one concrete example, the options, your recommendation.
- In a design doc, mark an open point with a **Decision needed** block (problem, example, options). List all open blocks in one section.

## Slice brief

Before the build, keep it short:

- `Goal`, `State` (date, brief or built, open decisions), `Depends`, `Builds`, `Decided`, `Open`.

Before code starts, add the details:

- `Read first, in full`: the files the builder must read.
- `Files`, `Contracts`, `How it works`, `Tests` (case by case), `Numbers` (what to measure and the target).

After the build, update it as built:

- Set `State` to built. Mark built parts with their file paths.
- `Carried`: work deferred from this slice and the slice that takes it. Add it to the `slices/README.md` carry-over in the same change.
- `Review round 1` and `Review round 2`: each finding and what was done with it.

## Slice steps

1. Brief.
2. Details.
3. Build.
4. Review round 1: three reviewers with different lenses (fit with the design, adversarial, simplicity).
5. Fix. A finding that needs a decision goes to the owner first.
6. Review round 2.
7. Walkthrough in `slices/NN/walkthrough/`: self-contained, code over prose, starts with the file list and sizes.
8. Owner review.
9. Update docs: the brief as built, `overview.md`, the names doc, `decisions.md`.

Docs, specs and decisions can be committed without owner review. Code waits for the owner review, unless repository rules say otherwise.

## Archive

`archive/README.md` states:

- The archive records how the design came about. Decisions and briefs win over it.
- Old names map to current names through the names doc.
- Which archived files current briefs still read, and which are record only.

## Handoff

Write a handoff only when the owner asks. Its first section is `Read first, in full`, a list of files.

## Package changelogs

For a repository that publishes packages, keep `CHANGELOG.md` per package with `## [Unreleased]` and the subsections `Breaking Changes`, `Added`, `Changed`, `Fixed`, `Removed`. A released section never changes.

## Before each commit

- Search current docs for each old or rejected name. Allow them in `archive/` and in the glossary’s `Not` column. Update each other current use.
- Each decision made in this change is in the decision log.
- Each index lists every file in its folder.
- No current doc describes removed behavior.
