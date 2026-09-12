Create a new GitHub Discussion in a repository.

With `--title`, `--body` (or `--body-file`), and `--category`, a discussion is created non-interactively.
Omitting any of these flags triggers interactive prompts when connected to a terminal.


USAGE
  gh discussion create [flags]

FLAGS
  -b, --body string              Body for the discussion
  -F, --body-file string         Read body text from file (use "-" to read from stdin)
  -c, --category string          Category name or slug for the discussion
  -l, --label strings            Labels to apply to the discussion
  -R, --repo [HOST/]OWNER/REPO   Select another repository using the [HOST/]OWNER/REPO format
  -t, --title string             Title for the discussion

INHERITED FLAGS
  --help   Show help for command

EXAMPLES
  # Create interactively
  $ gh discussion create

  # Create non-interactively
  $ gh discussion create --title "My question" --category "Q&A" --body "Details here"

LEARN MORE
  Use `gh <command> <subcommand> --help` for more information about a command.
  Read the manual at https://cli.github.com/manual
  Learn about exit codes using `gh help exit-codes`
  Learn about accessibility experiences using `gh help accessibility`
