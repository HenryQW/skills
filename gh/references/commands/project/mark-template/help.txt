Mark a project as a template

For more information about output formatting flags, see `gh help formatting`.

USAGE
  gh project mark-template [<number>] [flags]

FLAGS
      --format string     Output format: {json}
  -q, --jq expression     Filter JSON output using a jq expression
      --owner string      Login of the org owner.
  -t, --template string   Format JSON output using a Go template; see "gh help formatting"
      --undo              Unmark the project as a template.

INHERITED FLAGS
  --help   Show help for command

EXAMPLES
  # Mark the github org's project "1" as a template
  $ gh project mark-template 1 --owner "github"

  # Unmark the github org's project "1" as a template
  $ gh project mark-template 1 --owner "github" --undo

LEARN MORE
  Use `gh <command> <subcommand> --help` for more information about a command.
  Read the manual at https://cli.github.com/manual
  Learn about exit codes using `gh help exit-codes`
  Learn about accessibility experiences using `gh help accessibility`
