# Examples

  # Read a file from the default branch
  $ gh repo read-file README.md --repo cli/cli

  # Read a file at a specific ref
  $ gh repo read-file README.md --repo cli/cli --ref v2.50.0

  # Save a file to disk
  $ gh repo read-file README.md --repo cli/cli --output download/README.md

  # Print selected fields as JSON
  $ gh repo read-file README.md --repo cli/cli --json name,path,size,type

  # Read a file that contains terminal escape sequences
  $ gh repo read-file path/to/file --repo OWNER/REPO --allow-escape-sequences
