Create a project

For more information about output formatting flags, see `gh help formatting`.

USAGE
  gh project create [flags]

FLAGS
      --format string     Output format: {json}
  -q, --jq expression     Filter JSON output using a jq expression
      --owner string      Login of the owner. Use "@me" for the current user.
  -t, --template string   Format JSON output using a Go template; see "gh help formatting"
      --title string      Title for the project

INHERITED FLAGS
  --help   Show help for command

EXAMPLES
  # Create a new project owned by login monalisa
  $ gh project create --owner monalisa --title "a new project"

LEARN MORE
  Use `gh <command> <subcommand> --help` for more information about a command.
  Read the manual at https://cli.github.com/manual
  Learn about exit codes using `gh help exit-codes`
  Learn about accessibility experiences using `gh help accessibility`
