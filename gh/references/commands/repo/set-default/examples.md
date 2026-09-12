# Examples

  # Interactively select a default repository
  $ gh repo set-default

  # Set a repository explicitly
  $ gh repo set-default owner/repo

  # Set a repository using a git remote name
  $ gh repo set-default origin

  # View the current default repository
  $ gh repo set-default --view

  # Show more repository options in the interactive picker
  $ git remote add newrepo https://github.com/owner/repo
  $ gh repo set-default
