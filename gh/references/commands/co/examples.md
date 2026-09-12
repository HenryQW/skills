# Examples

  # Interactively select a PR from the 10 most recent to check out
  $ gh pr checkout

  # Checkout a specific PR
  $ gh pr checkout 32
  $ gh pr checkout https://github.com/OWNER/REPO/pull/32
  $ gh pr checkout feature
  $ gh pr checkout 32 --branch feature --worktree /path/to/wt-feature
