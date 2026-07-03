# Skills

Repository of custom skills.

| Name | Description | Install | Last updated (UTC) |
|---|---|---|---|
| `agent-aeo` | Implements agent-oriented website access patterns, including discovery metadata, markdown page views, llms.txt, and Accept negotiation. | `npx skills install HenryQW/skills agent-aeo -a codex -y` | 2026-05-10 12:32 |
| `agent-memory` | Sets up project-scoped agent memory and distills `.context/progress.md` into markdown Agent memory. | `npx skills install HenryQW/skills agent-memory -a codex -y` | 2026-07-01 20:11 |
| `gh-address-comments` | Addresses actionable GitHub PR review feedback using thread-aware review reads and focused local fixes. | `npx skills install HenryQW/skills gh-address-comments -a codex -y` | 2026-07-03 10:25 |
| `gh-fix-ci` | Debugs failing GitHub Actions PR checks with `gh`, log inspection, root-cause summaries, and approved focused fixes. | `npx skills install HenryQW/skills gh-fix-ci -a codex -y` | 2026-07-03 10:25 |
| `gh-pr-creation` | Creates or publishes GitHub or GitLab pull requests from the current branch with diff inspection, Conventional Commit titles, explicit push handling, and a fixed PR body template. | `npx skills install HenryQW/skills gh-pr-creation -a codex -y` | 2026-07-02 16:45 |
| `greptile-loop` | Runs compact Greptile review loops on the current branch and fixes actionable findings. | `npx skills install HenryQW/skills greptile-loop -a codex -y` | 2026-07-03 01:44 |
| `grill-to-issues` | Turns approved `$grill-with-docs` specs into dependency-aware GitHub child issues plus an implementation tracker issue and exactly one `final_check` child. | `npx skills install HenryQW/skills grill-to-issues -a codex -y` | 2026-07-01 20:45 |
| `issue-graph-runner` | Executes dependency-aware tracker child issues through `issue-to-code`, then routes PR CI and review cleanup to the right skills. | `npx skills install HenryQW/skills issue-graph-runner -a codex -y` | 2026-07-03 10:18 |
| `issue-to-code` | Implements a GitHub issue into a clean feature branch, runs Greptile review loops, commits, and hands off to `gh-pr-creation` after a clean pass. | `npx skills install HenryQW/skills issue-to-code -a codex -y` | 2026-07-03 01:44 |
| `review-repo` | Reviews a repository for evidence-backed maintainability, DRY, SOLID, testing, and architecture improvements without editing code. | `npx skills install HenryQW/skills review-repo -a codex -y` | 2026-07-02 17:51 |
| `triangulate` | Runs structured multi-agent evaluation workflows that generate, challenge, and adjudicate evidence-backed findings. | `npx skills install HenryQW/skills triangulate -a codex -y` | 2026-04-03 12:40 |
