# Examples

  # Have gh prompt you for what workflow you'd like to run and interactively collect inputs
  $ gh workflow run

  # Run the workflow file 'triage.yml' at the remote's default branch
  $ gh workflow run triage.yml

  # Run the workflow file 'triage.yml' at a specified ref
  $ gh workflow run triage.yml --ref my-branch

  # Run the workflow file 'triage.yml' with command line inputs
  $ gh workflow run triage.yml -f name=scully -f greeting=hello

  # Run the workflow file 'triage.yml' with JSON via standard input
  $ echo '{"name":"scully", "greeting":"hello"}' | gh workflow run triage.yml --json
