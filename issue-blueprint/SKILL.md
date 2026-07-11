---
name: issue-blueprint
description: Turn a rough multi-issue plan into a user-approved spec and dependency-aware GitHub issue graph. Use when asked to plan a multi-issue feature or create child issues plus a tracker and one final_check. Do not use for a standalone spec or glossary edit.
---

# Issue Blueprint

## Memory Boundary

- When the user invokes `issue-blueprint` directly, call `$agent-memory load` before Step 0 and `$agent-memory distill` as the final guard before every terminal return, including routing stops, access blockers, withheld approval, and successful publication.
- When a caller owns the memory boundary, skip both calls and preserve `.context/decisions.jsonl` for that caller.
- Append accepted durable product, domain, or architecture decisions as they are recorded in the planning bundle. Do not capture provisional options, issue mechanics, or routine planning details.
- Memory failure must not replace the issue-plan result or stop reason.

## Workflow

Run the smallest end-to-end path from a rough multi-issue plan to an approved GitHub issue graph.

0. Lock intent before work. If the user asks to use `$issue-blueprint`, create issues, or avoid implementation, treat the request as issue-graph planning only and do not start implementation prep.
1. Classify route before planning:
   - one known actionable GitHub issue → stop and route to `$issue-workbench #<issue>`;
   - clear multi-issue feature → continue;
   - standalone spec or glossary edit → stop; this workflow does not apply;
   - unclear target repository, spec location, or product behavior → ask for the missing decision before creating the planning bundle.
2. Read only the project instructions, active specs, glossary, repository state, and GitHub issue state needed to plan and publish. Discover facts from authoritative sources instead of asking the user. Check terminology against the project glossary and stress-test domain relationships with concrete scenarios.
3. Draft the complete planning bundle before review:
   - write the implementation handoff spec where the project stores specs;
   - update the glossary only when terminology changed;
   - create an ADR only for a hard-to-reverse, surprising decision with a real trade-off;
   - draft the provisional issue plan JSON using `references/issue-plan.md` and preserve non-goals;
   - render the provisional issue graph locally so the reviewer inspects the same bundle the user will approve.

```bash
python3 /path/to/issue-blueprint/scripts/render_issue_plan.py plan.json --out .context/issues
```

4. Run interactive blocker rounds until the reviewer returns `PASS`:
   1. Delegate exactly one read-only adversarial reviewer for the round using the template below. The reviewer must not edit files or question the user.
   2. Keep only blockers that make the plan ambiguous, incorrect, unsafe, untestable, poorly sliced, unnecessarily interfering, or improperly sequenced. Exclude cosmetic wording, optional cleanup, speculative future work, and preference-only implementation alternatives.
   3. Resolve factual blockers from the user prompt, project instructions, repository, issues, specs, glossary, or other authoritative evidence. Do not ask the user for discoverable facts; report an inaccessible authoritative source as an access blocker instead of recasting it as a product decision.
   4. Update the spec and issue plan, then re-render the graph after every factual resolution.
   5. Present unresolved product decisions in dependency order with context, a recommendation, and the consequences of each option. Ask dependent decisions one at a time. Batch at most five independent decisions and allow the user to accept all recommendations.
   6. Record each answer immediately in the spec and issue plan, then re-render the graph.
   7. Treat settled user decisions as authoritative. Reopen one only when new contradictory evidence is identified.
   8. Re-review only changed sections, unresolved blockers, and newly introduced contradictions. Start another round until no blocker remains.
5. Before publishing, mark excluded findings in `dropped_findings` with a short reason such as duplicate, solved, unclear, cleanup-only, or out-of-scope.
6. After zero blockers, show the user the spec path, issue titles and dependency waves, non-goals, target repository, and labels. Ask for explicit approval to publish this exact graph. Earlier plan approval is not publication approval.
7. Publish only after that approval. If approval is withheld or the graph changes, return to drafting, rendering, and blocker review; never publish the unapproved graph.
8. After approval, follow Issue Publishing.

## Reviewer Template

Pass exact paths so the reviewer inspects current artifacts rather than stale drafts.

```text
You are the only adversarial reviewer for this round.
Read these exact paths:
- implementation handoff spec: <absolute_spec_path>
- provisional issue plan: <absolute_plan_path>
- rendered issues: <absolute_rendered_issues_path>
- repository: <absolute_repo_path>

Remain read-only. Do not edit files or question the user.
Return PASS when there are no material blockers. Otherwise return at most five blockers, ordered by downstream dependency impact and then severity, using one line per blocker:
severity | kind | evidence | issue | recommended resolution

Only report ambiguity, incorrectness, unsafe behavior, untestability, poor slicing, avoidable interference, or improper sequencing. Treat micro-issues, separable mega-issues, and same-wave work with unnecessary shared surfaces as slicing blockers, not implementation preferences. Exclude cosmetic wording, optional cleanup, speculative future work, and preference-only implementation alternatives. Treat recorded user decisions as authoritative unless you cite new contradictory evidence.
```

## Token Discipline

- Pass file paths, not pasted documents, whenever the receiver can read the file.
- Subagents must not summarize the whole spec unless asked.
- After the first loop, review only changed sections, unresolved blockers, and newly introduced contradictions.
- The main agent owns blocker disposition, evidence gathering, user interaction, and all edits.
- User progress updates should be phase-level only: drafted, decisions needed, awaiting publication approval, publishing, published.

## Issue Publishing

1. Check labels before applying them:

```bash
gh label list --repo OWNER/REPO --limit 100
```

2. Publish children, then the implementation tracker, then updated child bodies:

```bash
python3 /path/to/issue-blueprint/scripts/publish_issue_plan.py plan.json --repo OWNER/REPO --label enhancement --label ready-for-agent --verify
```

`--verify` runs renderer and publisher self-tests, renders the plan, publishes the graph, writes `numbers.json`, and prints the Shipyard execution block. Do not run extra `gh issue view` checks after a successful `--verify`; use a single fallback check only if `--verify` reports an incomplete result or `numbers.json` is missing or malformed.

The publisher checkpoints `numbers.json` after each created issue and binds `publish-state.json` to the approved plan and repository. If publication fails, fix the cause and rerun the same command with `--resume`; a normal rerun stops rather than duplicating recorded issues, and resume rejects a changed plan or repository.

The publisher writes `.context/issues/numbers.json`:

```json
{"foundation":"#123","writer-boundary":"#124"}
```

It also prints the execution block to hand to Shipyard:

```text
execution:
parent_issue=#125
child_issues=#123 #124 #126
final_check_issue=#126
numbers_json=/absolute/repo/path/.context/issues/numbers.json
shipyard_worktree=/absolute/repo/path
shipyard_command=Use $shipyard #125
repo=OWNER/REPO
```

## Slicing Rules

- Prefer vertical tracer-bullet issues over layer-only work.
- Size each implementation issue around one cohesive, independently verifiable outcome. Merge incidental edits into the issue that owns their outcome instead of creating micro-issues for a few lines of work.
- Split large issues when they contain separable outcomes with distinct acceptance criteria, public seams, risks, or dependencies, or when their parts can be implemented independently. Keep them whole when splitting would create incomplete intermediate states or extra coordination.
- Treat changes of only a few lines or many hundreds or thousands of lines as review signals, not fixed thresholds. Explain in the issue `context` why an unusually small issue cannot be combined or an unusually large issue cannot be split.
- Within each dependency wave, minimize overlap in files, interfaces, and shared state so issues can be implemented in parallel with minimal coordination or merge conflicts.
- Do not add backward compatibility, migration layers, aliases, fallback paths, or future-proofing unless explicitly required by the issue, spec, or repo instructions.
- `tracker` is the implementation tracker issue. Use a title like `<version/topic> implementation tracker`.
- Default to the tight graph: tracker, the fewest cohesive, reasonably bounded, non-interfering implementation children, and one `final_check`.
- Every child issue must include `Tracker`, `What to build`, `Acceptance criteria`, `Testing`, `Blocked by`, `Blocks`, and `Parallelism`.
- Every child issue's `Parallelism` section must state why it is safe in its wave and identify any files, interfaces, or shared state expected to overlap with same-wave issues.
- Every child issue's `Testing` section must name the public seam under test, existing similar tests if known, the smallest validation command, and what not to test. If no useful seam exists, say so and provide a concrete non-test validation path.
- Exactly one child issue must have `"role": "final_check"`. It blocks nothing and is blocked by every other child issue.
- The implementation tracker issue must include the full issue graph and explicit waves for parallel execution.
- If findings were dropped before publish, record them in `dropped_findings`; the tracker will include a dropped-findings section.
- Publish blockers before blocked work so the final graph can use real issue numbers. The renderer topologically sorts `create-order.tsv` from `blocked_by`.
- Keep non-goals visible. They prevent compatibility paths and speculative scaffolding from sneaking back in.

## Verification

Run:

```bash
python3 /path/to/issue-blueprint/scripts/render_issue_plan.py --self-test
python3 /path/to/issue-blueprint/scripts/publish_issue_plan.py --self-test
python3 /path/to/skill-creator/scripts/quick_validate.py /path/to/issue-blueprint  # if available
```
