# Examples

  # Add a new named branch to the stack
  $ gh stack add my-feature

  # Add a branch and commit staged changes
  $ gh stack add -Am "Add user authentication" my-feature

  # Auto-generate branch name from the commit message
  $ gh stack add -m "Fix login bug"

  # Add a branch and open editor to write commit message
  $ gh stack add -A my-feature
