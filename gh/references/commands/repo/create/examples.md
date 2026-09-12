# Examples

  # Create a repository interactively
  $ gh repo create

  # Create a new remote repository and clone it locally
  $ gh repo create my-project --public --clone

  # Create a new remote repository in a different organization
  $ gh repo create my-org/my-project --public

  # Create a remote repository from the current directory
  $ gh repo create my-project --private --source=. --remote=upstream
