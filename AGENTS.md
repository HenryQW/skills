# Repository Maintenance Instructions

This repository stores skills used to automate development workflows.
These skills are meant for AI agents to execute, not for human readers. Keep instructions agent-facing, explicit, and operational rather than human-facing narrative documentation or diagrams.

## Organization

- Keep each skill in its own subfolder with its instruction file(s) and related assets.

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
