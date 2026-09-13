# Examples

  # List the root of the default branch
  $ gh repo read-dir --repo cli/cli

  # List a subdirectory
  $ gh repo read-dir docs --repo cli/cli

  # List a directory at a specific ref
  $ gh repo read-dir docs --repo cli/cli --ref v2.50.0

  # Print selected fields as JSON
  $ gh repo read-dir docs --repo cli/cli --json name,path,type,size
