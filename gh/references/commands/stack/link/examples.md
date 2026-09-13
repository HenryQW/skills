# Examples

  # Link branches into a stack (bottom to top)
  $ gh stack link auth-layer api-routes ui-components

  # Link existing PRs by number
  $ gh stack link 41 42 43

  # Link existing PRs by URL
  $ gh stack link https://github.com/owner/repo/pull/41 https://github.com/owner/repo/pull/42

  # Add PRs to the top of an existing stack (7 is a stack number)
  $ gh stack link 7 48 ui-polish

  # Specify a custom base branch for stack
  $ gh stack link --base develop auth-layer api-routes
