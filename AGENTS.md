# Repository Maintenance Instructions

This repository stores skills used to automate development workflows.
These skills are meant for AI agents to execute, not for human readers. Keep instructions agent-facing, explicit, and operational rather than human-facing narrative documentation or diagrams.

## Organization

- Keep each skill in its own subfolder with its instruction file(s) and related assets.

## Skill Quality

- When creating or updating skills, keep instructions compact, accurate, stable, and token-efficient.
- Prefer durable operational rules over verbose narrative, examples, or implementation details that agents can infer from the repository.

## Root README Requirement

The repository root `README.md` must include detailed skill information in a markdown table.

```md
| Name | Description | Install | Last updated (UTC) |
|---|---|---|---|
| `first-skill-name` | A short, plain-language description for the first skill. | `npx skills install HenryQW/skills first-skill-name -a codex -y` | YYYY-MM-DD HH:MM |
| `second-skill-name` | A short, plain-language description for the second skill. | `npx skills install HenryQW/skills second-skill-name -a codex -y` | YYYY-MM-DD HH:MM |
| `nth-skill-name` | A short, plain-language description for the nth skill. | `npx skills install HenryQW/skills nth-skill-name -a codex -y` | YYYY-MM-DD HH:MM |
```

## Change Policy (Mandatory)

Whenever a skill is added, removed, renamed, or modified, update the `README.md` in the same change.
When updating skills in this repository, do not preserve backward compatibility for legacy internal function interfaces in skill code. Specifically, do not preserve compatibility with:

- Previous function names.
- Previous variable names.
- Previous function signatures.

This rule applies to internal implementation APIs, not user-facing CLI or operational interfaces. CLI compatibility may be retained when required for safe rollout or existing workflows.

At minimum, update the root `README.md`:
- The `Install` column, with command `npx skills install HenryQW/skills <skill name> -a codex -y`.
- Any changed description(s).
- The `Last updated` timestamp in UTC, only update when the skill's implementation changes, not for documentation-only updates.

Do not leave README updates for a later commit.

## Context and precedence

- Before project work, read:
  - `${AGENT_MEMORY_ROOT}/projects/Skills/Agent/Memory/index.md`

## Execution

- When `$agent-memory` is invoked or progress distillation is requested, use `.context/progress.md` as the temporary source and write or update real markdown memory under `${AGENT_MEMORY_ROOT}/projects/Skills/Agent/Memory/` only when it contains durable context future agents would otherwise rediscover. Memory can include history, mistakes to avoid, rules, coding style, library preferences, and validation paths. Skip routine progress, duplicate lessons, and one-off mistakes.
