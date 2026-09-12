# Examples

  # Start a new stack targeting your default branch
  $ gh stack init

  # Or turn an existing set of branches into a stack
  $ gh stack init branch1 branch2 branch3

  # Make changes and commit, then add a branch to the stack
  $ gh stack add branch4

  # Push all branches and create/update PRs on GitHub
  $ gh stack submit

  # Keep your local in sync with remote
  $ gh stack sync
