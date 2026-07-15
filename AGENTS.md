# Repository Maintenance Instructions

This repository stores skills used to automate development workflows.
These skills are meant for AI agents to execute, not for human readers. Keep instructions agent-facing, explicit, and operational rather than human-facing narrative documentation or diagrams.

OBSIDIAN_PROJECT=`${OBSIDIAN_ROOT}/projects/Skills`

## Organization

- Keep each skill in its own subfolder with its instruction file(s) and related assets.

## Skill Quality

- When creating or updating skills, keep instructions compact, accurate, stable, and token-efficient.
- Prefer durable operational rules over verbose narrative, examples, or implementation details that agents can infer from the repository.

## Root README Requirement

The repository root `README.md` must include:

- One installation section near the top with `npx skills add HenryQW/skills`.
- One linked heading and short, plain-language introduction for every skill.
- `Workflow skills` and `Supporting skills` groups, each sorted A-Z by skill name.

Do not add inventory tables, per-skill install commands, update timestamps, or duplicate skill descriptions.

## Change Policy (Mandatory)

Whenever a skill is added, removed, renamed, or modified, update the `README.md` in the same change.
When updating skills in this repository, do not preserve backward compatibility for legacy internal function interfaces in skill code. Specifically, do not preserve compatibility with:

- Previous function names.
- Previous variable names.
- Previous function signatures.

This rule applies to internal implementation APIs, not user-facing CLI or operational interfaces. CLI compatibility may be retained when required for safe rollout or existing workflows.

At minimum, update the root `README.md`:
- Add, remove, rename, or revise the affected skill introduction.
- Keep the skill in the correct group and preserve A-Z ordering.
- Keep workflow guidance short and reference skill names instead of repeating each skill's role.

Do not leave README updates for a later commit.
