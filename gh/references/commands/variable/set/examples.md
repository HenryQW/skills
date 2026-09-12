# Examples

  # Add variable value for the current repository in an interactive prompt
  $ gh variable set MYVARIABLE

  # Read variable value from an environment variable
  $ gh variable set MYVARIABLE --body "$ENV_VALUE"

  # Read variable value from a file
  $ gh variable set MYVARIABLE < myfile.txt

  # Set variable for a deployment environment in the current repository
  $ gh variable set MYVARIABLE --env myenvironment

  # Set organization-level variable visible to both public and private repositories
  $ gh variable set MYVARIABLE --org myOrg --visibility all

  # Set organization-level variable visible to specific repositories
  $ gh variable set MYVARIABLE --org myOrg --repos repo1,repo2,repo3

  # Set multiple variables imported from the ".env" file
  $ gh variable set -f .env
