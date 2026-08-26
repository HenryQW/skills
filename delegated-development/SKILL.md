---
name: delegated-development
description: "Standard development process for agent-driven repos: main agent decomposes and orchestrates only; implementer/reviewer subagent pairs do the work in isolated worktrees with maximal safe parallelism, one PR per unit. Use for ALL dev tasks: features, refactors, bug fixes, cleanups."
---

# Delegated development: main orchestrates, subagent pairs do the work

The standard development process for repos developed by coding agents, for **all dev tasks** — features, refactors, fixes, cleanups. The main agent never implements; it decomposes work and orchestrates subagents. Subagents do the work in parallel wherever the units are independent. Harness-agnostic: bind the roles below to whatever delegation primitives your harness provides (parallel batches of subagents, implementer/reviewer roles).

```
task ──► main agent: decompose into bounded, independent units
              │
              ▼
         per unit: implementer ⇄ reviewer pair (parallel across units, chained within a unit)
              │ agree → validate → ship (one PR per unit)
              │ disagree/defects → rebuttal back to main agent
              ▼
         main agent: judge rebuttals & reviews, re-validate, delegate all remaining work back out
```

## Roles

- **Main agent** = orchestrator + final judge. Decomposes tasks, writes task packets, judges rebuttals and reviews, re-runs validation, inspects diffs. It does not edit code. Anything actionable left broken or unfinished goes back out as a new bounded delegation.
- **Implementer** = one bounded change. Reads the task packet, implements minimally, validates scoped checks/tests, reports changed files and risks.
- **Reviewer** = reviews a plan or diff for correctness, simplicity, safety, regressions. Pairs with implementers on substantive changes; skip reviewers for trivial changes (a few doc lines, mechanical renames).

## Decomposition rules

1. Break the task into the smallest units that are independently shippable as one PR each (typically one package/module or one cohesive cross-package change).
2. Independent units run concurrently; dependent units form a chain (implementer → reviewer → next implementer) rather than waiting on the main agent to sequence them manually.
3. Parallelism: run as many units as your delegation tool accepts per call; if unbounded, keep batches small enough (roughly ≤8–10) that each result still gets careful judgment. Overflow waits for the next batch.
4. Each task packet is self-contained: exact scope paths, the findings/spec, prior deliberate non-decisions, judgment-call caveats ("if the repo's CONTEXT/design docs say X is a product requirement, rebut"), validation commands, and shipping steps.

## Per-unit workflow

For every unit:

1. **Isolated worktree**: one git worktree and branch per unit so concurrent subagents never share a working tree:
   ```bash
   git fetch origin main
   git worktree add -b <prefix>/<unit> /tmp/agent-dev/<unit> origin/main
   ```
2. **Pair**: implementer implements; for substantive changes a reviewer then checks the diff (correctness, simplicity, safety, regressions). Reviewer findings go back to the implementer or, if contested, to the main agent as a rebuttal.
3. **Validation**: scoped typecheck/lint + scoped tests must pass before shipping.
4. **Version bump** if the repo publishes artifacts: follow the repo's own release policy (e.g. npm workspaces: `npm version patch --workspace packages/<pkg> --no-git-tag-version`, committing `package.json` and lockfile together). Docs-only changes usually don't warrant a release.
5. **Ship**: Conventional Commit, push the branch, `gh pr create --base main --body-file ...` listing what was applied and rebutted, with reasoning.

## Main-agent judgment

- Judge rebuttals and review disagreements against the code reasoning provided. Accepted ones stay unimplemented; wrong ones are overridden via a new delegation.
- Re-run scoped validation on every worktree afterward; inspect diffs. Delegate repair of anything broken/incomplete to a fresh subagent with a bounded packet (what was applied, what fails, what's missing such as a version bump).

## Finding scopes

Task classes that feed this workflow have thin scope docs defining what counts as a finding — e.g. over-engineering cleanup (`delete`/`stdlib`/`native`/`yagni`/`shrink` tags), correctness bugs, security holes, performance. Keep each scope doc to its finding taxonomy, hunt list, output format, and known judgment calls; do not duplicate workflow mechanics. Scope docs typically live in the target repo (`docs/agents/`) or alongside this skill.

## Operational notes (lessons from running this)

- **Model references** for delegation need `provider/model-id` form (e.g. `x-ai/grok-4.6`, `openai-codex/gpt-5.6-terra`) and thinking levels must match what the model supports in-session — check your harness's model registry/config when unsure.
- **Explicitly authorize push/PR** in the task packet ("the user has authorized you to commit, push, and run `gh pr create`"). Some subagents otherwise refuse network/git-write steps even when the task asks for them.
- **Subagents may fail silently or leave broken trees.** Always re-run scoped validation on every worktree afterward; delegate repair of any broken/incomplete work to a fresh subagent with a bounded task packet (what was applied, what fails, what's missing such as a version bump).
- **Shared lockfiles conflict**: every PR touching dependencies modifies them. Expect trivial merge-order conflicts between sibling PRs; rebase whichever merges second.
- **Commit messages with backticks**: write them to a temp file and use `git commit -F <file>` — inline `-m "..."` breaks on backticks/command substitution.
- **Repo-mandated hardening patterns** (config-safety rules, security checks) are not cleanup targets, even when they look duplicated.
