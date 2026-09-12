# Details

## Description

Render a skill's `SKILL.md` content in the terminal. This fetches the
skill file from the repository and displays it using the configured
pager, without installing anything.

A file tree is shown first, followed by the rendered `SKILL.md` content.
When running interactively and the skill contains additional files
(scripts, references, etc.), a file picker lets you browse them
individually.

When run with only a repository argument, lists available skills and
prompts for selection.

The skill argument can be a name, a namespaced name (`author/skill`),
or an exact path within the repository (`skills/author/skill`,
`packages/agent-skills/code-review`, or any `.../SKILL.md` path).
Namespaced names with one slash are matched by name. Use a `SKILL.md`
suffix to force a one-directory path outside the standard conventions.

To preview a specific version of the skill, append `@VERSION` to the
skill name. The version is resolved as a git tag, branch, or commit SHA.
