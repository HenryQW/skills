# Repository Maintenance Instructions

This repository stores skills used to automate development workflows.

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
1. first skill name, a short, plain-language description for the first skill. Last updated: <YYYY-MM-DD HH:MM in UTC>.
2. second skill name, a short, plain-language description for the second skill. Last updated: <YYYY-MM-DD HH:MM in UTC>.
...
n. nth skill name, a short, plain-language description for the nth skill. Last updated: <YYYY-MM-DD HH:MM in UTC>.
```

## Change Policy (Mandatory)

Whenever a skill is added, removed, renamed, or modified, update the folder `README.md` in the same change.

At minimum, update:

- The root `README.md` folder list when folder-level contents change.
- The root `README.md` subfolder description text to exactly match each subfolder README description.
- The skill list.
- Any changed description(s).
- The `Last updated` timestamp in UTC.

Do not leave README updates for a later commit.
