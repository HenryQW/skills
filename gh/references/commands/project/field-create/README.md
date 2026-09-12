Create a field in a project

For more information about output formatting flags, see `gh help formatting`.

USAGE
  gh project field-create [<number>] [flags]

FLAGS
      --data-type string                DataType of the new field.: {TEXT|SINGLE_SELECT|DATE|NUMBER}
      --format string                   Output format: {json}
  -q, --jq expression                   Filter JSON output using a jq expression
      --name string                     Name of the new field
      --owner string                    Login of the owner. Use "@me" for the current user.
      --single-select-options strings   Options for SINGLE_SELECT data type
  -t, --template string                 Format JSON output using a Go template; see "gh help formatting"

INHERITED FLAGS
  --help   Show help for command

EXAMPLES
  # Create a field in the current user's project "1"
  $ gh project field-create 1 --owner "@me" --name "new field" --data-type "text"

  # Create a field with three options to select from for owner monalisa
  $ gh project field-create 1 --owner monalisa --name "new field" --data-type "SINGLE_SELECT" --single-select-options "one,two,three"

LEARN MORE
  Use `gh <command> <subcommand> --help` for more information about a command.
  Read the manual at https://cli.github.com/manual
  Learn about exit codes using `gh help exit-codes`
  Learn about accessibility experiences using `gh help accessibility`
