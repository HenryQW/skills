# Skills

🚢 Automated engineering workflows for Codex.

Give an agent a plan, issue, branch, or pull request. These skills can carry it through analysis, implementation, checks, review, and publication while stopping for decisions and approvals that need a human.

## 📦 Installation

Install every skill for Codex:

```bash
npx skills add HenryQW/skills
```

## ✨ Why use them

- Automate complete workflows instead of isolated coding steps.
- Keep changes scoped with branches, worktrees, checks, and review gates.
- Preserve evidence so later steps can reuse valid results instead of repeating work.

## ⚙️ Requirements

- GitHub workflows require authenticated `gh`.
- `greptile` is optional; `review-checkpoint` falls back to adversarial review when unavailable.

## 🧭 Choose a workflow

```mermaid
flowchart TD
  request["Request"] --> load["agent-memory load"]
  load --> route{"Select route"}
  route -->|Repo audit| survey["repo-surveyor"]
  survey --> blueprint["issue-blueprint"]
  route -->|Multi-issue plan| blueprint
  blueprint -->|Approved issue graph| shipyard["shipyard"]
  shipyard --> workbench["issue-workbench"]
  route -->|One known issue| workbench
  workbench --> checkpoint["review-checkpoint"]
  checkpoint --> launch["pr-launchpad"]
  route -->|Current branch needs PR| launch
  route -->|Existing PR| health{"PR health"}
  launch --> health
  health -->|CI failing| ci["ci-repairbay"]
  ci --> health
  health -->|Review feedback| repair["review-repairbay"]
  repair --> health
  health -->|Clear| done["Mergeable"]
  route -->|Missing decision| distill["agent-memory distill"]
  done --> distill
```

Start with the smallest route that fits:

- One actionable issue: `issue-workbench #<issue>`
- A repository audit: `repo-surveyor`, then `issue-blueprint` if you want issues created
- A multi-issue feature: `issue-blueprint`, then `shipyard #<parent>`
- A branch ready to publish: `pr-launchpad`
- A pull request blocked by checks or review: `ci-repairbay` or `review-repairbay`

## 🤖 What each skill automates

### 🚀 Workflow skills

#### [`ci-repairbay`](ci-repairbay/)

Inspects failing GitHub Actions checks, then makes and verifies a focused fix only when asked. Inspection remains read-only.

#### [`issue-blueprint`](issue-blueprint/)

Turns a rough multi-issue plan into an approved GitHub issue graph with checks, dependencies, and a final verification issue.

#### [`issue-workbench`](issue-workbench/)

Takes one GitHub issue through scoped implementation, checks, and blocker review, then opens a PR or returns a `shipyard` handoff.

#### [`pr-launchpad`](pr-launchpad/)

Publishes a finished branch: inspect the diff, validate the current commit, commit and push pending work, then create a consistent PR.

#### [`repo-surveyor`](repo-surveyor/)

Read-only repository maintainability audit with ranked, file-level findings.

#### [`review-checkpoint`](review-checkpoint/)

Runs blocker-only review using Greptile or an independent fallback, records the exact commit result, and applies fixes only when authorized.

#### [`review-repairbay`](review-repairbay/)

Clears unresolved PR feedback through inspection, focused fixes, replies, and thread resolution, then rechecks until none remain.

#### [`shipyard`](shipyard/)

Takes a parent issue to one integration PR: run dependency-ready child worktrees, merge them, verify and review the result, then publish.

### 🧰 Supporting skills

#### [`agent-aeo`](agent-aeo/)

Adds or audits public discovery files, Markdown routes, and headers so AI agents can read a website reliably.

#### [`agent-memory`](agent-memory/)

Loads only task-relevant project context, then saves durable decisions and results. Any Markdown folder can provide the memory layer; see the [`agent-memory` setup guide](agent-memory/references/setup.md).

#### [`identify-optimizations`](identify-optimizations/)

Read-only architecture audit that ranks up to five improvements in an HTML report with before-and-after diagrams.

#### [`skill-optimizer`](skill-optimizer/)

Finds waste or unreliable behavior in an existing skill, applies the smallest root-cause improvement, and verifies representative cases.

## 📄 License

Apache License 2.0.
See [LICENSE](LICENSE).
