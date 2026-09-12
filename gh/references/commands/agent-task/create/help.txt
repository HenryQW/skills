Create an agent task (preview)

USAGE
  gh agent-task create [<task description>] [flags]

FLAGS
  -b, --base string              Base branch for the pull request (use default branch if not provided)
  -a, --custom-agent string      Use a custom agent for the task. e.g., use 'my-agent' for the 'my-agent.md' agent
      --follow                   Follow agent session logs
  -F, --from-file file           Read task description from file (use "-" to read from standard input)
  -R, --repo [HOST/]OWNER/REPO   Select another repository using the [HOST/]OWNER/REPO format

INHERITED FLAGS
  --help   Show help for command

EXAMPLES
  # Create a task from an inline description
  $ gh agent-task create "build me a new app"

  # Create a task from an inline description and follow logs
  $ gh agent-task create "build me a new app" --follow

  # Create a task from a file
  $ gh agent-task create -F task-desc.md

  # Create a task with problem statement from stdin
  $ echo "build me a new app" | gh agent-task create -F -

  # Create a task with an editor
  $ gh agent-task create

  # Create a task with an editor and a file as a template
  $ gh agent-task create -F task-desc.md

  # Select a different base branch for the PR
  $ gh agent-task create "fix errors" --base branch

  # Create a task using the custom agent defined in '.github/agents/my-agent.md'
  $ gh agent-task create "build me a new app" --custom-agent my-agent

LEARN MORE
  Use `gh <command> <subcommand> --help` for more information about a command.
  Read the manual at https://cli.github.com/manual
  Learn about exit codes using `gh help exit-codes`
  Learn about accessibility experiences using `gh help accessibility`
