Edit a GitHub Discussion.

Without flags, the command runs interactively when connected to a terminal.
Use flags to update specific fields non-interactively.


USAGE
  gh discussion edit {<number> | <discussion-url>} [flags]

FLAGS
      --add-label name           Add labels by name
  -b, --body string              New body for the discussion
  -F, --body-file string         Read body text from file (use "-" to read from standard input)
  -c, --category string          New category name or slug for the discussion
      --remove-label name        Remove labels by name
  -R, --repo [HOST/]OWNER/REPO   Select another repository using the [HOST/]OWNER/REPO format
  -t, --title string             New title for the discussion

INHERITED FLAGS
  --help   Show help for command

EXAMPLES
  # Edit interactively
  $ gh discussion edit 123

  # Update title, body, and category
  $ gh discussion edit 123 --title "Updated title" --body "Updated body" --category "Ideas"

  # Update body from a file
  $ gh discussion edit 123 --body-file body.md

  # Add and remove labels
  $ gh discussion edit 123 --add-label "bug,help wanted" --remove-label "stale"

LEARN MORE
  Use `gh <command> <subcommand> --help` for more information about a command.
  Read the manual at https://cli.github.com/manual
  Learn about exit codes using `gh help exit-codes`
  Learn about accessibility experiences using `gh help accessibility`
