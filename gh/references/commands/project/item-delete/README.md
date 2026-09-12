Delete an item from a project by ID

For more information about output formatting flags, see `gh help formatting`.

USAGE
  gh project item-delete [<number>] [flags]

FLAGS
      --format string     Output format: {json}
      --id string         ID of the item to delete
  -q, --jq expression     Filter JSON output using a jq expression
      --owner string      Login of the owner. Use "@me" for the current user.
  -t, --template string   Format JSON output using a Go template; see "gh help formatting"

INHERITED FLAGS
  --help   Show help for command

EXAMPLES
  # Delete an item in the current user's project "1"
  $ gh project item-delete 1 --owner "@me" --id <item-id>

LEARN MORE
  Use `gh <command> <subcommand> --help` for more information about a command.
  Read the manual at https://cli.github.com/manual
  Learn about exit codes using `gh help exit-codes`
  Learn about accessibility experiences using `gh help accessibility`
