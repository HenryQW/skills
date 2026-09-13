# Examples

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
