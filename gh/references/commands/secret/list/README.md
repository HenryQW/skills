# gh secret list

List secrets on one of the following levels: - repository (default): available to GitHub Actions runs, Agents sessions, or Dependabot in a repository - environment: available to GitHub Actions runs for a deployment environment in a repository - organization: available to GitHub Actions runs, Agents sessions, Dependabot, or Codespaces within an organization - user: available to Codespaces for your user

**Usage:** `gh secret list [flags]`

**Aliases:** `gh secret ls`

## Options
  -a, --app string        List secrets for a specific application: {actions|agents|codespaces|dependabot}
  -e, --env string        List secrets for an environment
  -q, --jq expression     Filter JSON output using a jq expression
      --json fields       Output JSON with the specified fields
  -o, --org string        List secrets for an organization
  -t, --template string   Format JSON output using a Go template; see "gh help formatting"
  -u, --user              List a secret for your user
  -R, --repo [HOST/]OWNER/REPO   Select another repository using the [HOST/]OWNER/REPO format

## More
- [Details](details.md)
