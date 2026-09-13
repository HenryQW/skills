# Examples

  # Paste secret value for the current repository in an interactive prompt
  $ gh secret set MYSECRET

  # Read secret value from an environment variable
  $ gh secret set MYSECRET --body "$ENV_VALUE"

  # Set secret for a specific remote repository
  $ gh secret set MYSECRET --repo origin/repo --body "$ENV_VALUE"

  # Read secret value from a file
  $ gh secret set MYSECRET < myfile.txt

  # Set secret for a deployment environment in the current repository
  $ gh secret set MYSECRET --env myenvironment

  # Set organization-level secret visible to both public and private repositories
  $ gh secret set MYSECRET --org myOrg --visibility all

  # Set organization-level secret visible to specific repositories
  $ gh secret set MYSECRET --org myOrg --repos repo1,repo2,repo3

  # Set organization-level secret visible to no repositories
  $ gh secret set MYSECRET --org myOrg --no-repos-selected

  # Set user-level secret for Codespaces
  $ gh secret set MYSECRET --user

  # Set repository-level secret for Dependabot
  $ gh secret set MYSECRET --app dependabot

  # Set multiple secrets imported from the ".env" file
  $ gh secret set -f .env

  # Set multiple secrets from stdin
  $ gh secret set -f - < myfile.txt
