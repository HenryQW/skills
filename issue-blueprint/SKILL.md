---
name: issue-blueprint
description: Turn a rough multi-issue plan into a user-approved spec and dependency-aware GitHub issue graph. Use when asked to plan a multi-issue feature or create child issues plus a tracker and one final_check. Do not use for a standalone spec or glossary edit.
---

# Issue Blueprint

Turn a rough multi-issue plan into an approved GitHub issue graph without implementing it.

## Memory

Direct invocation owns `$agent-memory load`. Distill only on final `Done`, `Stop`,
or `Blocked`; approval, publication-resume, `PENDING`, and `PENDING_REVIEW`
returns preserve `.context/decisions.jsonl` without distilling. Nested invocation
always preserves it for its caller. Capture only accepted durable product,
domain, or architecture decisions; memory failure does not change the result.

## Workflow

1. Route before planning:
   - one known actionable issue -> `$issue-workbench #<issue>`;
   - clear multi-issue feature -> continue;
   - standalone spec or glossary edit -> stop;
   - missing repository, spec location, or product behavior -> discover authoritative facts, then ask only for unresolved product decisions.
2. Read only relevant project instructions, specs, glossary, repository state,
   issue state, and any supplied Repo Surveyor report. A Surveyor handoff is
   evidence, not a plan: Issue Blueprint alone owns issue-plan JSON, slicing,
   dependencies, child validation, adversarial review, and publication. Use
   project terminology and test domain relationships with concrete scenarios.
3. Draft the provisional bundle:
   - implementation handoff spec in the project's spec location;
   - glossary changes only for changed terms and an ADR only for a surprising, hard-to-reverse trade-off;
   - issue-plan JSON conforming to `references/issue-plan.md`, including non-goals and any `dropped_findings`;
   - locally rendered issue graph.
   Do not create or switch branches, commit, or run target-repository validation while the bundle is provisional. The caller owns the single planning commit after finalization.
4. Run blocker rounds with exactly one read-only adversarial reviewer per round. Pass exact artifact and repository paths. The first round must trace every acceptance criterion to concrete evidence and enforce the issue-plan slicing rules. Resolve discoverable facts from authoritative sources; report inaccessible sources as access blockers and ask the user only for material product decisions. Record answers, update the bundle, and re-render before reviewing only changed or unresolved material.
5. After `PASS`, show the exact spec path, target repository, issue titles, dependency waves, labels, and non-goals. Publish only after explicit approval of that exact graph; earlier plan approval is not publication approval.
6. If approval is withheld or the graph changes, keep the bundle provisional and return to review. Otherwise publish and finalize as below.

## Reviewer contract

The reviewer remains read-only, does not question the user, and returns `PASS` or at most five material blockers ordered by dependency impact and severity:

```text
severity | kind | evidence | issue | recommended resolution
```

Only ambiguity, incorrectness, unsafe behavior, untestability, poor slicing, avoidable interference, or improper sequencing are blockers. Recorded user decisions remain authoritative absent cited contradictory evidence. Missing concrete evidence for an acceptance criterion is an untestability blocker.

## Publish and finalize

Check requested labels, then run:

```bash
python3 <skill_dir>/scripts/publish_issue_plan.py plan.json --repo OWNER/REPO --label enhancement --label ready-for-agent --verify
```

`--verify` self-tests, renders, publishes children then tracker, writes
`.context/issues/numbers.json`, and prints only the absolute working directory
and `Use $shipyard #<parent>` handoff. Do not duplicate successful verification
with `gh issue view`.

The publisher checkpoints each issue and binds its state to the approved plan and repository. On partial failure, fix the cause and rerun the same command with `--resume`; never republish from a changed plan or repository.

Approval withheld or publication incomplete leaves the spec provisional. After complete publication, set an existing spec lifecycle marker to exactly `Approved and published`; do not invent one. Retry failed local finalization without republishing. Only then may the caller create the single planning commit.

## Graph rules

- Prefer the fewest cohesive, independently verifiable, non-interfering vertical children; keep non-goals visible and avoid unrequested compatibility or future-proofing.
- Use the schema and validation ownership in `references/issue-plan.md` as the sole issue-shape contract.
- The tracker contains the complete graph and explicit waves. Publish blockers before blocked work so bodies can use real issue numbers.
- `final_check` is the only multi-child integration check. Return defects to the implementation child that owns the failed criterion.

## Output discipline

Pass paths instead of pasted artifacts, keep progress phase-level, and never summarize unchanged documents. The main agent owns evidence, blocker disposition, user decisions, and edits.
