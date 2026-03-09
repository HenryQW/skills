# review

Skills for reviewing artifacts, surfacing issues, and adjudicating claims.

## Skills
| Name | Description | Install | Last updated (UTC) |
|---|---|---|---|
| `issue_adversary` | Adversarially attacks each `issue_finder` claim using the original artifacts and returns whether the claim is actually rebutted. | `npx skills install HenryQW/skills issue_adversary -a codex -y` | 2026-03-09 10:00 |
| `issue_finder` | Scans supplied material for a high-recall superset of plausible issues and returns evidence-grounded findings only. | `npx skills install HenryQW/skills issue_finder -a codex -y` | 2026-03-09 09:50 |
| `issue_referee` | Makes the final evidence-based ruling on candidate issues by comparing the original artifacts with the finder and adversary outputs. | `npx skills install HenryQW/skills issue_referee -a codex -y` | 2026-03-09 09:50 |
| `issue_review_pipeline` | Orchestrates `issue_finder`, `issue_adversary`, and `issue_referee` end to end, forwarding artifacts and stage outputs unchanged and returning only the referee rulings. | `npx skills install HenryQW/skills issue_review_pipeline -a codex -y` | 2026-03-09 10:09 |
