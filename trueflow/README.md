# trueflow
Skills for generic multi-agent evaluation workflows that generate, challenge, and adjudicate findings.

## Skills
| Name | Description | Install | Last updated (UTC) |
|---|---|---|---|
| `trueflow` | Orchestrates `trueflow_initializer`, `trueflow_adversary`, and `trueflow_referee` end to end, persists stage files under `.context/trueflow/`, and returns a consolidated findings table. | `npx install HenryQW/skills trueflow -a codex -y` | 2026-03-09 13:15 |
| `trueflow_adversary` | Adversarially attacks each `trueflow_initializer` finding using the original artifacts and writes its review to `.context/trueflow/adversary.md`. | `npx install HenryQW/skills trueflow_adversary -a codex -y` | 2026-03-09 13:15 |
| `trueflow_initializer` | Produces a high-recall first-pass set of evidence-grounded findings about supplied artifacts and writes them to `.context/trueflow/initializer.md`. | `npx install HenryQW/skills trueflow_initializer -a codex -y` | 2026-03-09 13:15 |
| `trueflow_referee` | Makes the final evidence-based ruling on candidate findings and writes it to `.context/trueflow/referee.md`. | `npx install HenryQW/skills trueflow_referee -a codex -y` | 2026-03-09 13:15 |
