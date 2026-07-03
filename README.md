# Autoship

Agent skills for moving planned engineering work from rough input to mergeable pull request.

Autoship is a small workflow fleet. Each skill owns one leg of the route: survey the repo, blueprint the issues, build one issue, launch the PR, repair CI or review feedback, and let `shipyard` coordinate the crossing. Codex is the default target, but the instructions are plain enough for comparable agents.

## Workflow Map

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
  shipyard --> ready{"Unblocked child?"}
  ready -->|No| blocked["Report blockers"]
  ready -->|Yes| workbench["issue-workbench"]
  workbench --> pr["Pull request"]
  pr --> health{"PR clean?"}
  health -->|CI failing| ci_repair["ci-repairbay"]
  health -->|Review comments| review_repair["review-repairbay"]
  health -->|Yes| mergeable["Mergeable code"]
  ci_repair --> health
  review_repair --> health
  mergeable --> complete["Merged or verified complete"]
  complete --> final_done{"Was final_check?"}
  final_done -->|Yes| done["Done"]
  final_done -->|No| more{"More children?"}
  more -->|Yes| shipyard
  more -->|No| final["final_check"]
  final --> workbench
```

## Workflows

### Audit to Issue Plan

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

### Plan to Issue Graph

Use this when the starting point is a rough plan that needs hard questioning before implementation.

```mermaid
flowchart LR
  plan["Rough plan"] --> blueprint["issue-blueprint"]
  blueprint --> spec["Spec"]
  blueprint --> children["Child issues"]
  blueprint --> parent["Parent issue"]
  children --> final["final_check"]
```

- Run `issue-blueprint`.
- Produce the spec, dependency-aware child issues, parent issue, and one `final_check` child.

### Issue Graph to Pull Requests

Use this after a parent issue exists and implementation should proceed one child issue at a time.

```mermaid
flowchart TD
  parent["Parent issue"] --> shipyard["shipyard"]
  shipyard --> ready{"Unblocked child?"}
  ready -->|No| blocked["Report blockers"]
  ready -->|Yes| workbench["issue-workbench"]
  workbench --> pr["Pull request"]
  pr --> cleanup{"Needs cleanup?"}
  cleanup -->|CI| ci_repair["ci-repairbay"]
  cleanup -->|Review| review_repair["review-repairbay"]
  cleanup -->|No| done["Ready"]
  ci_repair --> cleanup
  review_repair --> cleanup
```

- Run `shipyard`.
- Let it choose the next unblocked child and route implementation through `issue-workbench`.
- Do not stack PRs unless the parent issue explicitly requires it.
- Run `final_check` only after all other children are merged or verified complete.

### Pull Request to Mergeable

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
- Re-check the PR after each cleanup pass.

## Skill Reference

This table is the canonical skill inventory: category, purpose, install command, and last implementation update.

| Category | Name | Purpose | Install | Last updated (UTC) |
|---|---|---|---|---|
| Planning | `repo-surveyor` | Audit a repo for maintainability problems without editing code. | `npx skills install HenryQW/skills repo-surveyor -a codex -y` | 2026-07-03 14:39 |
| Planning | `issue-blueprint` | Create dependency-aware child issues, one parent issue, and exactly one `final_check`. | `npx skills install HenryQW/skills issue-blueprint -a codex -y` | 2026-07-03 14:39 |
| Execution | `shipyard` | Advance a parent issue by running ready children through PRs. | `npx skills install HenryQW/skills shipyard -a codex -y` | 2026-07-03 14:39 |
| Execution | `issue-workbench` | Implement one GitHub issue on a clean branch and open a reviewed PR. | `npx skills install HenryQW/skills issue-workbench -a codex -y` | 2026-07-03 14:39 |
| Review gate | `review-checkpoint` | Run Greptile on the current branch and fix actionable findings. | `npx skills install HenryQW/skills review-checkpoint -a codex -y` | 2026-07-03 14:39 |
| PR publishing | `pr-launchpad` | Publish the current branch as a GitHub or GitLab pull request. | `npx skills install HenryQW/skills pr-launchpad -a codex -y` | 2026-07-03 14:39 |
| PR cleanup | `ci-repairbay` | Diagnose and fix failing GitHub Actions PR checks. | `npx skills install HenryQW/skills ci-repairbay -a codex -y` | 2026-07-03 14:39 |
| PR cleanup | `review-repairbay` | Resolve actionable GitHub PR review feedback. | `npx skills install HenryQW/skills review-repairbay -a codex -y` | 2026-07-03 14:39 |
| Support | `agent-memory` | Set up and distill project-scoped Agent memory. | `npx skills install HenryQW/skills agent-memory -a codex -y` | 2026-07-01 20:11 |
| Support | `agent-aeo` | Add or audit public website access patterns for AI agents. | `npx skills install HenryQW/skills agent-aeo -a codex -y` | 2026-05-10 12:32 |
