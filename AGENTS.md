# Repository Maintenance Instructions

This repository stores skills used to automate development workflows.
These skills are meant for AI agents to execute, not for human readers. Keep instructions agent-facing, explicit, and operational rather than human-facing narrative documentation or diagrams.

## Organization

- Organize skills by folder (for example: `gh/`, `python/`, `frontend/`).
- Keep each skill in its own subfolder with its instruction file(s) and related assets.

## Root README Requirement

The repository root `README.md` must include a list of top-level skill folders with a brief description only.

- The root README description for each subfolder must be exactly the same as that subfolder README's top description text.
- Treat the subfolder README description as the source of truth; if they differ, update the root README to match the subfolder README.
- Do not include per-skill implementation details in the root `README.md`.
- Put detailed skill information in the corresponding subfolder `README.md`.

## Folder README Requirement

Each folder that contains skills must have a `README.md`, with the following structure:

```md
# <Folder name>
Description of the folder's theme and purpose.

## Skills
| Name | Description | Install | Last updated (UTC) |
|---|---|---|---|
| `first-skill-name` | A short, plain-language description for the first skill. | `npx skills install HenryQW/skills first-skill-name -a codex -y` | YYYY-MM-DD HH:MM |
| `second-skill-name` | A short, plain-language description for the second skill. | `npx skills install HenryQW/skills second-skill-name -a codex -y` | YYYY-MM-DD HH:MM |
| `nth-skill-name` | A short, plain-language description for the nth skill. | `npx skills install HenryQW/skills nth-skill-name -a codex -y` | YYYY-MM-DD HH:MM |
```

## Change Policy (Mandatory)

Whenever a skill is added, removed, renamed, or modified, update the folder `README.md` in the same change.
When updating skills in this repository, do not preserve backward compatibility for legacy internal function interfaces in skill code. Specifically, do not preserve compatibility with:

- Previous function names.
- Previous variable names.
- Previous function signatures.

This rule applies to internal implementation APIs, not user-facing CLI or operational interfaces. CLI compatibility may be retained when required for safe rollout or existing workflows.

At minimum, update:

- The root `README.md` folder list when folder-level contents change.
- The root `README.md` subfolder description text to exactly match each subfolder README description.
- The `## Skills` table rows.
- The `Install` column, with command `npx skills install HenryQW/skills <skill name> -a codex`.
- Any changed description(s).
- The `Last updated` timestamp in UTC, only update then the skill's implementation changes, not for documentation-only updates.

Do not leave README updates for a later commit.
