---
name: issue-blueprint
description: Turn a rough plan into a grilled spec and dependency-aware GitHub issue graph. Use when asked to create specs, glossary updates, child issues, a tracker issue, or one final_check issue.
---

# Issue Blueprint

## Workflow

Run the smallest end-to-end path from design pressure-test to GitHub issue graph.

0. Lock intent before work. If the user asks to use `$issue-blueprint`, create issues, or avoid implementation, state the boundary in one line: no code changes, issue graph only. Do not start implementation prep.
1. Read only the project instructions, active specs, and GitHub issue state needed to publish. If the user's bullets are enough to draft the graph, proceed. Ask at most one blocking clarification.
2. Use `$grill-with-docs` for the spec loop.
3. Run the spec loop:
   - Main agent is the reviewer and scope owner.
   - Subagent A runs `$grill-with-docs` with the Reviewer A template below and returns at most 5 findings per loop.
   - Main agent debates Subagent A until they produce a final spec with explicit assumptions, non-goals, acceptance criteria, open questions, and glossary/domain updates. Batch obvious correctness axes in the first draft: field shapes, invariants, failure modes, domain semantics, dependencies, and side-effect boundaries.
   - Subagent B reviews that final spec with the Reviewer B template below and returns at most 5 findings per loop.
   - Main agent decides whether Subagent B's findings are worth addressing. Address findings that change correctness, constraints, acceptance criteria, dependencies, implementation risk, or user-stated scope. Reject speculative or overbuilt findings with a short rationale.
   - If any finding is worth addressing, patch once and loop back to the Main-agent/Subagent-A debate only for deterministic blockers.
   - Stop when Subagent B raises no new issue worth addressing, or after 5 total spec-review loops. If the loop limit is reached, stop and ask the human to intervene.
4. Write the minimum durable docs where the project stores specs. If no location is known, ask. Required outputs are:
   - implementation handoff spec,
   - glossary/domain model update only when terminology changed.
5. Stop and ask if findings conflict with user-stated scope or require a product decision the agents cannot make.
6. Draft an issue plan JSON using `references/issue-plan.md`. Before publish, mark excluded findings in `dropped_findings` with a short reason such as duplicate, solved, unclear, cleanup-only, or out-of-scope.
7. Render issue markdown:

```bash
python3 /path/to/issue-blueprint/scripts/render_issue_plan.py plan.json --out .context/issues
```

8. Publish with `publish_issue_plan.py --verify`; it creates children first, then the tracker, then updates children with real numbers. Treat `--verify` plus `.context/issues/numbers.json` as sufficient verification unless the command fails or the numbers file is missing.

## Reviewer Templates

Use these prompts so reviewers inspect current artifacts, not stale drafts.

Reviewer A:

```text
Use $grill-with-docs on this exact draft/spec path: <absolute_path>.
Working directory: <absolute_repo_path>.
Return at most 5 findings in this shape only:
BLOCKERS:
- severity | issue | exact change

ACCEPTED:
- change

REJECTED:
- reason
```

Reviewer B:

```text
Review this final spec and issue-plan draft only:
- spec: <absolute_path>
- plan_json: <absolute_path>
- working_directory: <absolute_repo_path>
Do not review old drafts or unrelated repo cleanup.
Return at most 5 deterministic blockers in the same shape.
```

## Token Discipline

- Pass file paths, not pasted documents, whenever the receiver can read the file.
- Subagents must not summarize the whole spec unless asked.
- After the first loop, review only changed sections, unresolved findings, and newly introduced contradictions.
- Main agent records only accepted/rejected findings and one-line rationale.
- User progress updates should be phase-level only: drafted, review blockers, publishing, published.

## Issue Publishing

1. Check labels before applying them:

```bash
gh label list --repo OWNER/REPO --limit 100
```

2. Publish children, then the implementation tracker, then updated child bodies:

```bash
python3 /path/to/issue-blueprint/scripts/publish_issue_plan.py plan.json --repo OWNER/REPO --label enhancement --label ready-for-agent --verify
```

`--verify` runs renderer and publisher self-tests, renders the plan, publishes the graph, writes `numbers.json`, prints the Shipyard execution block, and verifies every published issue with `gh issue view`. Do not run extra `gh issue view` checks after a successful `--verify`; use a single fallback check only if `--verify` reports an incomplete result.

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
- `tracker` is the implementation tracker issue. Use a title like `<version/topic> implementation tracker`.
- Default to the tight graph: tracker, the minimum implementation children that can be worked independently, and one `final_check`.
- Every child issue must include `Tracker`, `What to build`, `Acceptance criteria`, `Blocked by`, `Blocks`, and `Parallelism`.
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

For live publishing, run the `publish_issue_plan.py --verify` command above and report its execution block.
