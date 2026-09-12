# Examples

  # List branches for issue 123
  $ gh issue develop --list 123

  # List branches for issue 123 in repo cli/cli
  $ gh issue develop --list --repo cli/cli 123

  # Create a branch for issue 123 based on the my-feature branch
  $ gh issue develop 123 --base my-feature

  # Create a branch for issue 123 and check it out
  $ gh issue develop 123 --checkout

  # Create a branch for issue 123 and check it out in a worktree
  $ gh issue develop 123 --checkout --worktree /path/to/wt-feature

  # Create a branch in repo monalisa/cli for issue 123 in repo cli/cli
  $ gh issue develop 123 --repo cli/cli --branch-repo monalisa/cli
