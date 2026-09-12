Add a pull request or an issue to a project

For more information about output formatting flags, see `gh help formatting`.

USAGE
  gh project item-add [<number>] [flags]

FLAGS
      --format string     Output format: {json}
  -q, --jq expression     Filter JSON output using a jq expression
      --owner string      Login of the owner. Use "@me" for the current user.
  -t, --template string   Format JSON output using a Go template; see "gh help formatting"
      --url string        URL of the issue or pull request to add to the project

INHERITED FLAGS
  --help   Show help for command

EXAMPLES
  # Add an item to monalisa's project "1"
  $ gh project item-add 1 --owner monalisa --url https://github.com/monalisa/myproject/issues/23

LEARN MORE
  Use `gh <command> <subcommand> --help` for more information about a command.
  Read the manual at https://cli.github.com/manual
  Learn about exit codes using `gh help exit-codes`
  Learn about accessibility experiences using `gh help accessibility`
