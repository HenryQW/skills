# Skills

<h1 align="center">
  🚢 Shipping ideas into production.
</h1>

A collection of skills for harness engineering and loop engineering: 🚢 shipping ideas into production.

These skills are small, composable workflow harnesses.
Each one owns one leg of the loop: survey the repo, blueprint the issues, build one issue, launch the PR, repair CI or review feedback, and let `shipyard` coordinate the route.

Supports Codex and other agents that use `npx skills` manage skills.

## 🧭 Workflow Map

```mermaid
flowchart TD
  rough["Rough plan"] --> blueprint["issue-blueprint"]
  audit["Repo review request"] --> surveyor["repo-surveyor"]
  surveyor --> reduce["Reduced findings"]
  reduce --> approved{"Approved issue plan?"}
  approved -->|Yes| blueprint
  approved -->|No| stop["Stop"]
  blueprint --> parent["Parent issue"]
  parent --> children["Dependency-aware child issues"]
  children --> shipyard["shipyard"]
  shipyard --> default_branch{"Current branch is default?"}
  default_branch -->|Yes| default_stop["Stop: switch to integration branch"]
  default_branch -->|No| ready{"Unblocked child?"}
  ready -->|No| blocked["Report blockers"]
  ready -->|Yes| worktrees["Ready-wave child worktrees"]
  worktrees --> integrate["Current shipyard branch"]
  integrate --> recheck{"Newly unblocked child?"}
  recheck -->|Yes| worktrees
  recheck -->|No| final_branch["final_check worktree"]
  final_branch --> final_merge["Merge or skip final_check"]
  final_merge --> final_pr["Final shipyard pull request"]
  final_pr --> health
  health -->|CI failing| ci_repair["ci-repairbay"]
  health -->|Review comments| review_repair["review-repairbay"]
  health -->|Yes| mergeable["Mergeable code"]
  ci_repair --> health
  review_repair --> health
  mergeable --> done["Done"]
```

## 🔁 Workflows

### 🔍 Audit to Issue Plan

Use this when the starting point is "audit this repo" and the output should become approved issue work.

```mermaid
flowchart LR
  audit["Audit request"] --> surveyor["repo-surveyor"]
  surveyor --> reduce["Reduced findings"]
  reduce --> approve{"Approved?"}
  approve -->|Yes| blueprint["issue-blueprint"]
  approve -->|No| stop["Stop"]
```

- Run `repo-surveyor`.
- Merge findings by touched area and verification boundary.
- Drop cleanup-only work or fold it into nearby valuable work.
- Use `issue-blueprint` only after the reduced issue list is approved.

### 🧱 Plan to Issue Graph

Use this when the starting point is a rough plan that needs hard questioning before implementation.

```mermaid
flowchart LR
  plan["Rough plan"] --> blueprint["issue-blueprint"]
  blueprint --> spec["Spec"]
  blueprint --> children["Child issues"]
  blueprint --> parent["Parent issue"]
  children --> final["final_check"]
```

- Run `issue-blueprint` with `$grill-with-docs` available.
- Produce the spec, dependency-aware child issues, parent issue, and one `final_check` child.

### 🚢 Issue Graph to Pull Requests

Use this after a parent issue exists and implementation should proceed through the current non-default integration branch.

```mermaid
flowchart TD
  parent["Parent issue"] --> shipyard["shipyard"]
  shipyard --> mode{"Current branch is default?"}
  mode -->|Yes| default_stop["Stop: switch to integration branch"]
  mode -->|No| ready{"Unblocked child?"}
  ready -->|No| blocked["Report blockers"]
  ready -->|Yes| worktrees["Ready-wave child worktrees"]
  worktrees --> integrate["Merge into current branch"]
  integrate --> recheck{"Newly unblocked child?"}
  recheck -->|Yes| worktrees
  recheck -->|No| final_branch["final_check worktree"]
  final_branch --> final_merge["Merge or skip final_check"]
  final_merge --> final_pr["Final shipyard pull request"]
  final_pr --> cleanup
  cleanup -->|CI| ci_repair["ci-repairbay"]
  cleanup -->|Review| review_repair["review-repairbay"]
  cleanup -->|No| done["Ready"]
  ci_repair --> cleanup
  review_repair --> cleanup
```

- Run `shipyard #<parent>`.
- Stop on the default branch; switch to a non-default integration branch before execution.
- Create worktrees only for the current ready dependency wave, merge review-clean branches back into the shipyard branch, then re-inspect for newly unblocked children.
- Run `final_check` only after all other children are merged or verified complete.

### 🛠️ Pull Request to Mergeable

Use this when a PR already exists and needs to become mergeable.

```mermaid
flowchart LR
  pr["Pull request"] --> check{"Blocked by?"}
  check -->|CI| ci_repair["ci-repairbay"]
  check -->|Review| review_repair["review-repairbay"]
  check -->|Neither| clean["Mergeable"]
  ci_repair --> verify["Re-check PR"]
  review_repair --> verify
  verify --> check
```

- Use `ci-repairbay` for failing GitHub Actions checks.
- Use `review-repairbay` for unresolved review threads or requested changes.
- If the only non-green signal is a known unavailable external review check that the user or caller explicitly waived or replaced, record `Pending external unavailable check: <check>` instead of invoking repair skills.
- Re-check the PR after each cleanup pass.

## 📦 Skill Reference

This table is the canonical skill inventory: category, purpose, install command, and last implementation update.

| Category | Name | Purpose | Install | Last updated (UTC) |
|---|---|---|---|---|
| Planning | `repo-surveyor` | Audit a repo for maintainability problems without editing code. | `npx skills install HenryQW/skills repo-surveyor -a codex -y` | 2026-07-04 15:35 |
| Planning | `issue-blueprint` | Create dependency-aware child issues, one parent issue, and exactly one `final_check`. | `npx skills install HenryQW/skills issue-blueprint -a codex -y` | 2026-07-04 15:35 |
| Execution | `shipyard` | Advance a parent issue from a non-default integration branch through dependency-wave child worktrees into one final PR. | `npx skills install HenryQW/skills shipyard -a codex -y` | 2026-07-04 21:26 |
| Execution | `issue-workbench` | Implement one issue with guarded diffs and a review fallback. | `npx skills install HenryQW/skills issue-workbench -a codex -y` | 2026-07-04 15:35 |
| Review gate | `review-checkpoint` | Run Greptile, or fallback adversarial review, and fix actionable findings. | `npx skills install HenryQW/skills review-checkpoint -a codex -y` | 2026-07-04 15:35 |
| PR publishing | `pr-launchpad` | Publish the current branch as a GitHub or GitLab pull request. | `npx skills install HenryQW/skills pr-launchpad -a codex -y` | 2026-07-04 13:57 |
| PR cleanup | `ci-repairbay` | Diagnose and fix failing GitHub Actions PR checks. | `npx skills install HenryQW/skills ci-repairbay -a codex -y` | 2026-07-04 05:48 |
| PR cleanup | `review-repairbay` | Resolve actionable GitHub PR review feedback. | `npx skills install HenryQW/skills review-repairbay -a codex -y` | 2026-07-04 06:05 |
| Support | `agent-memory` | Set up and distill project-scoped Agent memory. | `npx skills install HenryQW/skills agent-memory -a codex -y` | 2026-07-04 05:53 |
| Support | `agent-aeo` | Add or audit public website access patterns for AI agents. | `npx skills install HenryQW/skills agent-aeo -a codex -y` | 2026-07-04 05:44 |

## 📄 License

Apache License 2.0.
See [LICENSE](LICENSE).
