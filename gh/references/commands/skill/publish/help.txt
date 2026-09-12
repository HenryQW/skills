Validate a local repository's skills against the Agent Skills specification
and publish them by creating a GitHub release.

Skills are discovered using the same conventions as install:

  - `skills/*/SKILL.md`
  - `skills/{scope}/*/SKILL.md`
  - `*/SKILL.md` (root-level)
  - `plugins/{scope}/skills/*/SKILL.md`

Validation checks include:

  - Skill names match the strict agentskills.io naming rules
  - Each skill name matches its directory name
  - Required frontmatter fields (name, description) are present
  - allowed-tools is a string, not an array
  - Install metadata (`metadata.github-*`) is stripped if present

After validation passes, publish will interactively guide you through:

  - Adding the `agent-skills` topic to the repository
  - Choosing a version tag (semver recommended)
  - Creating a GitHub release with auto-generated notes

Use `--dry-run` to validate without publishing.
Use `--tag` to publish non-interactively with a specific tag.
Use `--fix` to automatically strip install metadata from committed files
without publishing. Review and commit the changes, then run publish again.


USAGE
  gh skill publish [<directory>] [flags]

FLAGS
  --dry-run      Validate without publishing
  --fix          Auto-fix issues where possible without publishing (e.g. strip install metadata)
  --tag string   Version tag for the release (e.g. v1.0.0)

INHERITED FLAGS
  --help   Show help for command

EXAMPLES
  # Validate and publish interactively
  $ gh skill publish

  # Publish with a specific tag (non-interactive)
  $ gh skill publish --tag v1.0.0

  # Validate only (no publish)
  $ gh skill publish --dry-run

  # Strip install metadata without publishing
  $ gh skill publish --fix

LEARN MORE
  Use `gh <command> <subcommand> --help` for more information about a command.
  Read the manual at https://cli.github.com/manual
  Learn about exit codes using `gh help exit-codes`
  Learn about accessibility experiences using `gh help accessibility`
