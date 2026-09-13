# gh variable delete

Delete a variable on one of the following levels: - repository (default): available to GitHub Actions runs or Dependabot in a repository - environment: available to GitHub Actions runs for a deployment environment in a repository - organization: available to GitHub Actions runs or Dependabot within an organization

**Usage:** `gh variable delete <variable-name> [flags]`

**Aliases:** `gh variable remove`

## Options
  -e, --env string   Delete a variable for an environment
  -o, --org string   Delete a variable for an organization
  -R, --repo [HOST/]OWNER/REPO   Select another repository using the [HOST/]OWNER/REPO format
