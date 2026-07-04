---
name: issue-blueprint
description: Turn a rough plan into a grilled spec, dependency graph, implementation tracker issue, final check issue, and GitHub child issue set. Requires grill-with-docs. Use when the user asks to use grill-with-docs plus subagents, create a spec/glossary, slice work into blocked/blocking GitHub issues, or publish a dependency-aware implementation issue graph.
---

# Issue Blueprint

## Workflow

Run the smallest end-to-end path from design pressure-test to GitHub issue graph.

1. Read project instructions, active specs, and GitHub issue state. If unclear, ask only the blocking question.
2. Require `$grill-with-docs`. If unavailable, stop and tell the user this skill requires `$grill-with-docs`.
3. Run the spec loop:
   - Main agent is the reviewer and scope owner.
   - Subagent A runs `$grill-with-docs` and returns at most 5 findings per loop.
   - Main agent debates Subagent A until they produce a final spec with explicit assumptions, non-goals, acceptance criteria, open questions, and glossary/domain updates.
   - Subagent B reviews that final spec and returns at most 5 findings per loop.
   - Main agent decides whether Subagent B's findings are worth addressing. Address findings that change correctness, constraints, acceptance criteria, dependencies, implementation risk, or user-stated scope. Reject speculative or overbuilt findings with a short rationale.
   - If any finding is worth addressing, loop back to the Main-agent/Subagent-A debate.
   - Stop when Subagent B raises no new issue worth addressing, or after 5 total spec-review loops. If the loop limit is reached, stop and ask the human to intervene.
4. Write the minimum durable docs where the project stores specs. If no location is known, ask. Required outputs are:
   - implementation handoff spec,
   - glossary/domain model update only when terminology changed.
5. Stop and ask if findings conflict with user-stated scope or require a product decision the agents cannot make.
6. Draft an issue plan JSON using `references/issue-plan.md`.
7. Render issue markdown:

```bash
python3 /path/to/issue-blueprint/scripts/render_issue_plan.py plan.json --out .context/issues
```

8. Create child issues first, then the implementation tracker issue, then re-render children with real numbers and update them.

## Token Discipline

- Pass file paths, not pasted documents, whenever the receiver can read the file.
- Subagents must not summarize the whole spec unless asked.
- After the first loop, review only changed sections, unresolved findings, and newly introduced contradictions.
- Subagent findings must be actionable and use this compact shape: severity, issue, exact change.
- Main agent records only accepted/rejected findings and one-line rationale.
- Review returns must use this compact shape:

```md
BLOCKERS:
- severity | issue | exact change

ACCEPTED:
- change

REJECTED:
- reason
```

## Issue Publishing

Publishing requires the GitHub CLI (`gh`) authenticated for the target repo.

1. Check labels before applying them:

```bash
gh label list --repo OWNER/REPO --limit 100
```

2. Publish children, then the implementation tracker, then updated child bodies:

```bash
python3 /path/to/issue-blueprint/scripts/publish_issue_plan.py \
  plan.json \
  --repo OWNER/REPO \
  --label enhancement \
  --label ready-for-agent
```

3. Verify the returned issue graph with `gh issue view`.

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
shipyard_worktree=/absolute/repo/path
shipyard_command=Use $shipyard #125
repo=OWNER/REPO
```

## Slicing Rules

- Prefer vertical tracer-bullet issues over layer-only work.
- `tracker` is the implementation tracker issue. Use a title like `<version/topic> implementation tracker`.
- Every child issue must include `Tracker`, `What to build`, `Acceptance criteria`, `Blocked by`, `Blocks`, and `Parallelism`.
- Exactly one child issue must have `"role": "final_check"`. It blocks nothing and is blocked by every other child issue.
- The implementation tracker issue must include the full issue graph and explicit waves for parallel execution.
- Publish blockers before blocked work so the final graph can use real issue numbers. The renderer topologically sorts `create-order.tsv` from `blocked_by`.
- Keep non-goals visible. They prevent compatibility paths and speculative scaffolding from sneaking back in.

## Verification

Run:

```bash
python3 /path/to/issue-blueprint/scripts/render_issue_plan.py --self-test
python3 /path/to/issue-blueprint/scripts/publish_issue_plan.py --self-test
python3 /path/to/skill-creator/scripts/quick_validate.py /path/to/issue-blueprint  # if available
```

After publishing, verify with `gh issue view` or the GitHub connector and report the publisher's execution block.
