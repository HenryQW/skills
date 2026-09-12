List agent tasks (preview)

For more information about output formatting flags, see `gh help formatting`.

USAGE
  gh agent-task list [flags]

FLAGS
  -q, --jq expression     Filter JSON output using a jq expression
      --json fields       Output JSON with the specified fields
  -L, --limit int         Maximum number of agent tasks to fetch (default 30)
  -t, --template string   Format JSON output using a Go template; see "gh help formatting"
  -w, --web               Open agent tasks in the browser

INHERITED FLAGS
  --help   Show help for command

JSON FIELDS
  completedAt, createdAt, id, name, pullRequestNumber, pullRequestState,
  pullRequestTitle, pullRequestUrl, repository, state, updatedAt, user

LEARN MORE
  Use `gh <command> <subcommand> --help` for more information about a command.
  Read the manual at https://cli.github.com/manual
  Learn about exit codes using `gh help exit-codes`
  Learn about accessibility experiences using `gh help accessibility`
