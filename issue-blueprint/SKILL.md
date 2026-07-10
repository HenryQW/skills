---
name: issue-blueprint
description: Turn a rough plan into a grilled spec and dependency-aware GitHub issue graph. Use when asked to create specs, glossary updates, child issues, a tracker issue, or one final_check issue.
---

# Issue Blueprint

## Workflow

Run the smallest end-to-end path from design pressure-test to GitHub issue graph.

0. Lock intent before work. If the user asks to use `$issue-blueprint`, create issues, or avoid implementation, state the boundary in one line: no code changes, issue graph only. Do not start implementation prep.
1. Classify route before planning:
   - one known actionable GitHub issue → stop and route to `$issue-workbench #<issue>`;
   - clear multi-issue feature → continue;
   - unclear destination or product behavior → ask for the missing decision before creating an issue graph.
2. Read only the project instructions, active specs, and GitHub issue state needed to publish. If the user's bullets are enough to draft the graph, proceed. Ask at most one blocking clarification.
3. Use `$grill-with-docs` for the spec loop.
4. Run the spec loop:
   - Main agent is the reviewer and scope owner.
   - Subagent A runs `$grill-with-docs` with the Reviewer A template below and returns at most 5 deterministic blockers per loop.
   - Main agent resolves blockers only from the user prompt, project instructions, live repo/issue/spec context, relevant memory, or reviewer evidence. Do not guess.
   - Accept evidence-backed blockers, reject speculative/cosmetic/cleanup-only/out-of-scope blockers with a short rationale, and ask the user when resolution requires a product decision or cannot be inferred.
   - Patch accepted blockers once. Re-run Subagent A only if accepted blockers materially changed the graph.
   - Stop when no accepted blockers remain. Do not add a second reviewer by default.
5. Write the minimum durable docs where the project stores specs. If no location is known, ask. Required outputs are:
   - implementation handoff spec,
   - glossary/domain model update only when terminology changed.
6. Stop and ask if blockers conflict with user-stated scope or require a product decision the agents cannot make.
7. Draft an issue plan JSON using `references/issue-plan.md`. Before publish, mark excluded findings in `dropped_findings` with a short reason such as duplicate, solved, unclear, cleanup-only, or out-of-scope.
8. Render issue markdown:

```bash
python3 /path/to/issue-blueprint/scripts/render_issue_plan.py plan.json --out .context/issues
```

9. Publish with `publish_issue_plan.py --verify`; it creates children first, then the tracker, then updates children with real numbers. Treat `--verify` plus `.context/issues/numbers.json` as sufficient verification unless the command fails or the numbers file is missing.

## Reviewer Templates

Use these prompts so reviewers inspect current artifacts, not stale drafts.

Reviewer A:

```text
Use $grill-with-docs on this exact draft/spec path: <absolute_path>.
Working directory: <absolute_repo_path>.
Return at most 5 deterministic blockers in this shape only:
BLOCKERS:
- severity | issue | exact change

ACCEPTED:
- change

REJECTED:
- reason
```

## Token Discipline

- Pass file paths, not pasted documents, whenever the receiver can read the file.
- Subagents must not summarize the whole spec unless asked.
- After the first loop, review only changed sections, unresolved blockers, and newly introduced contradictions.
- Main agent records only accepted/rejected blockers and one-line rationale.
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

`--verify` runs renderer and publisher self-tests, renders the plan, publishes the graph, writes `numbers.json`, and prints the Shipyard execution block. Do not run extra `gh issue view` checks after a successful `--verify`; use a single fallback check only if `--verify` reports an incomplete result or `numbers.json` is missing or malformed.

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
- Do not add backward compatibility, migration layers, aliases, fallback paths, or future-proofing unless explicitly required by the issue, spec, or repo instructions.
- `tracker` is the implementation tracker issue. Use a title like `<version/topic> implementation tracker`.
- Default to the tight graph: tracker, the minimum implementation children that can be worked independently, and one `final_check`.
- Every child issue must include `Tracker`, `What to build`, `Acceptance criteria`, `Testing`, `Blocked by`, `Blocks`, and `Parallelism`.
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

For live publishing, run the `publish_issue_plan.py --verify` command above and report its execution block.
