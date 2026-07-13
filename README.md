# 🛠️ Skills

Composable, agent-run workflows for taking repository work from first look to merge-ready pull request.

Use one skill for a focused job, or connect them as a guarded harness: each skill owns one stage, passes verified state forward, and stops when another skill should take over.

## 📦 Installation

```bash
npx skills add HenryQW/skills
```

## ⚙️ Requirements

- GitHub workflows require authenticated `gh`.
- `greptile` is optional; `review-checkpoint` falls back to local adversarial review when unavailable.

## 🧭 How the harness works

Choose the smallest entry point that matches the work. Skills can run alone; the arrows show their explicit handoffs when they run together.

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
  repair --> health
  health -->|Yes| done["Merge-ready"]
  done -->|Approved engineering reasoning| distill["agent-memory distill"]
```

When skills are nested, the outer workflow stays in charge. `shipyard` launches child work, ingests their handoffs, batches integration, and delegates PR repair without giving up ownership.

Common starting points:

- One actionable issue: `issue-workbench #<issue>`
- A repository audit: `repo-surveyor`; add issue planning only when you want a handoff to `issue-blueprint`
- A multi-issue feature: `issue-blueprint`, then `shipyard #<parent>`
- A branch ready to publish: `pr-launchpad`
- A pull request blocked by checks or review: `ci-repairbay` or `review-repairbay`

## 🤖 Meet the skills

### 🚀 Workflow skills

#### [🧯 `ci-repairbay`](ci-repairbay/)

Reads failing GitHub Actions checks, applies a scoped fix only when asked, and returns the branch to its owning PR workflow.

#### [🗺️ `issue-blueprint`](issue-blueprint/)

Turns a rough feature into an approved, dependency-aware issue graph whose published parent is ready for `shipyard`.

#### [🔧 `issue-workbench`](issue-workbench/)

Implements and reviews one issue, then either publishes a standalone PR or returns a verified child handoff to `shipyard`.

#### [🚀 `pr-launchpad`](pr-launchpad/)

Publishes the inspected branch as a consistently formatted PR, reusing a matching existing PR when safe.

#### [🔭 `repo-surveyor`](repo-surveyor/)

Audits a repository without editing it, produces an HTML/Mermaid report, and optionally hands evidence to `issue-blueprint`.

#### [🛡️ `review-checkpoint`](review-checkpoint/)

Runs one blocker-only review per commit through Greptile or one adversarial fallback, then returns pass, pending, or blockers.

#### [🩹 `review-repairbay`](review-repairbay/)

Fixes selected review feedback or, when explicitly delegated, clears actionable threads and verifies none remain.

#### [🚢 `shipyard`](shipyard/)

Runs an approved issue graph through frozen child waves, batch integration, final checks, one PR, and its repair loop.

### 🧰 Supporting skills

#### [🌐 `agent-aeo`](agent-aeo/)

Adds or audits shared discovery, Markdown, and plain-text routes for public website content.

#### [🧠 `agent-memory`](agent-memory/)

Loads approved project context before work and distills the accepted reasoning behind code, architecture, and optimization choices after terminal completion; see the [setup guide](agent-memory/references/setup.md).

#### [✂️ `skill-optimizer`](skill-optimizer/)

Finds evidenced waste in an existing skill, applies the smallest root-cause fix, and verifies representative behavior.

## 📄 License

Apache License 2.0.
See [LICENSE](LICENSE).
