# 🛠️ Skills

Composable, agent-run workflows for taking repository work from first look to merge-ready pull request.

Use one skill for a focused job, or connect them as a guarded harness: each skill owns one stage, passes verified state forward, and stops when another skill should take over.

## 📦 Installation

```bash
npx skills add HenryQW/skills
```

## ⚙️ Requirements

- GitHub workflows require authenticated `gh`.

## 🧭 How the harness works

Choose the smallest entry point that matches the work. Skills can run alone; the arrows below show their explicit handoffs when they run together.

### Ⓜ️🅰️❎ Automation

1. `issue-blueprint` turns a rough idea, feature, or bug into an issue graph.
1. Approve or revise the plan.
1. `shipyard` handles the rest while you sip coffee.
1. Review and approve the PR.

### Granular Routing

- One actionable issue: `issue-workbench #<issue>`
- A repository audit: `repo-surveyor`; add issue planning only when you want a handoff to `issue-blueprint`
- A basic GitHub pull request: `git-pr`; workflow-managed branch: `pr-launchpad`
- A pull request blocked by checks: `ci-repairbay`; selected review repair: `review-repairbay`; full review sweep: `pr-comment-sweep`

```mermaid
flowchart TD
  request["What needs doing?"] --> context{"Need project context?"}
  context -->|Yes| load["agent-memory load"]
  context -->|No| route{"Choose the smallest route"}
  load --> route
  route -->|Audit a repository| survey["repo-surveyor"]
  survey -->|Planning explicitly requested| blueprint["issue-blueprint"]
  route -->|Plan multiple issues| blueprint
  blueprint -->|Approved and published parent| shipyard["shipyard"]
  route -->|Implement one issue| workbench["issue-workbench"]
  shipyard -->|Launch frozen child wave| workbench
  workbench --> checkpoint["review-checkpoint"]
  checkpoint --> owner{"Who owns integration?"}
  owner -->|Standalone branch| launch["pr-launchpad"]
  owner -->|Shipyard child handoff| shipyard
  shipyard -->|Integrated exact head passes| launch
  route -->|Publish current branch| launch
  route -->|Repair an existing PR| health
  launch --> health
  health{"PR healthy?"} -->|CI failing| ci["ci-repairbay"]
  ci --> health
  health -->|Review feedback| repair["review-repairbay"]
  route -->|Sweep all PR feedback| sweep["pr-comment-sweep"]
  sweep --> health
  repair --> health
  health -->|Yes| done["Merge-ready"]
  done -->|Durable decisions or guidance| distill["agent-memory distill"]
```

When skills are nested, the outer workflow stays in charge. `shipyard` launches child work, ingests their handoffs, batches integration, and delegates PR repair without giving up ownership.

## 🤖 Meet the skills

### 🚀 Workflow skills

#### [🧯 `ci-repairbay`](ci-repairbay/)

Diagnoses failing GitHub Actions checks and applies the smallest scoped fix only when explicitly requested.

#### [🗺️ `issue-blueprint`](issue-blueprint/)

Builds a dependency-aware issue graph and publishes it only after approval of the exact plan.

#### [🔧 `issue-workbench`](issue-workbench/)

Implements one issue, runs a native subagent review, then publishes a PR or returns a verified `shipyard` handoff.

#### [🗣️ `pr-comment-sweep`](pr-comment-sweep/)

Sweeps PR feedback with bundled helpers, retrying snapshots, evidence-led triage, safe push, and thread resolution.

#### [🚀 `pr-launchpad`](pr-launchpad/)

Publishes the inspected branch, reusing HEAD-bound validation and one matching PR when safe.

#### [🔭 `repo-surveyor`](repo-surveyor/)

Produces a clear, read-only, evidence-backed HTML maintainability report and optionally hands findings to `issue-blueprint`.

#### [🛡️ `review-checkpoint`](review-checkpoint/)

Reviews one named local branch head through a native read-only subagent and returns pass or blockers.

#### [🩹 `review-repairbay`](review-repairbay/)

Fixes selected review feedback with focused validation or clears actionable threads when explicitly authorized.

#### [🚢 `shipyard`](shipyard/)

Runs an approved issue graph through subagent-reviewed child branches, frozen waves, one final parent review, and one repairable PR.

### 🧰 Supporting skills

#### [🌐 `agent-aeo`](agent-aeo/)

Adds or audits shared discovery, Markdown, and plain-text routes for public website content.

#### [🧠 `agent-memory`](agent-memory/)

Loads confirmed project context, preserves candidates across resumable work, and writes approved decisions and guidance directly to Obsidian; see the [setup guide](agent-memory/references/setup.md).

#### [🔎 `beanquery`](beanquery/)

Runs quick read-only BQL queries against existing Beancount ledgers.

#### [💾 `git-commit`](git-commit/)

Creates coherent scoped Conventional Commits from changes against the target branch.

#### [🔀 `git-pr`](git-pr/)

Creates focused GitHub pull requests from inspected branch changes.

#### [🧩 `pi-extension-workbench`](pi-extension-workbench/)

Builds and repairs Pi extensions against version-matched docs and examples from installed Pi; includes a reusable authority resolver.

#### [✂️ `skill-optimizer`](skill-optimizer/)

Finds evidenced waste in an existing skill, applies the smallest root-cause fix, and verifies representative behavior.

#### [🔄 `update-from-main`](update-from-main/)

Safely syncs current worktree branch with remote `main`.

## 📄 License

Apache License 2.0.
See [LICENSE](LICENSE).
