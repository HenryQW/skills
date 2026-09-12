Display labels in a GitHub repository.

When using the `--search` flag results are sorted by best match of the query.
This behavior cannot be configured with the `--order` or `--sort` flags.

For more information about output formatting flags, see `gh help formatting`.

USAGE
  gh label list [flags]

ALIASES
  gh label ls

FLAGS
  -q, --jq expression     Filter JSON output using a jq expression
      --json fields       Output JSON with the specified fields
  -L, --limit int         Maximum number of labels to fetch (default 30)
      --order string      Order of labels returned: {asc|desc} (default "asc")
  -S, --search string     Search label names and descriptions
      --sort string       Sort fetched labels: {created|name} (default "created")
  -t, --template string   Format JSON output using a Go template; see "gh help formatting"
  -w, --web               List labels in the web browser

INHERITED FLAGS
      --help                     Show help for command
  -R, --repo [HOST/]OWNER/REPO   Select another repository using the [HOST/]OWNER/REPO format

JSON FIELDS
  color, createdAt, description, id, isDefault, name, updatedAt, url

EXAMPLES
  # Sort labels by name
  $ gh label list --sort name

  # Find labels with "bug" in the name or description
  $ gh label list --search bug

LEARN MORE
  Use `gh <command> <subcommand> --help` for more information about a command.
  Read the manual at https://cli.github.com/manual
  Learn about exit codes using `gh help exit-codes`
  Learn about accessibility experiences using `gh help accessibility`
