# Examples

  # Rebase the entire stack
  $ gh stack rebase

  # Only rebase from trunk to the current branch
  $ gh stack rebase --downstack

  # Only rebase from current branch to the top
  $ gh stack rebase --upstack

  # Rebase stack branches without pulling from or rebasing with trunk
  $ gh stack rebase --no-trunk

  # Continue after resolving conflicts
  $ gh stack rebase --continue

  # Abort and restore all branches
  $ gh stack rebase --abort
