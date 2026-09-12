# gh secret delete

Delete a secret on one of the following levels: - repository (default): available to GitHub Actions runs, Agents sessions, or Dependabot in a repository - environment: available to GitHub Actions runs for a deployment environment in a repository - organization: available to GitHub Actions runs, Agents sessions, Dependabot, or Codespaces within an organization - user: available to Codespaces for your user

**Usage:** `gh secret delete <secret-name> [flags]`

**Aliases:** `gh secret remove`

## Options
  -a, --app string   Delete a secret for a specific application: {actions|agents|codespaces|dependabot}
  -e, --env string   Delete a secret for an environment
  -o, --org string   Delete a secret for an organization
  -u, --user         Delete a secret for your user
  -R, --repo [HOST/]OWNER/REPO   Select another repository using the [HOST/]OWNER/REPO format
