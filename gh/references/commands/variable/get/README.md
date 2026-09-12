# gh variable get

Get a variable on one of the following levels: - repository (default): available to GitHub Actions runs or Dependabot in a repository - environment: available to GitHub Actions runs for a deployment environment in a repository - organization: available to GitHub Actions runs or Dependabot within an organization

**Usage:** `gh variable get <variable-name> [flags]`

## Options
  -e, --env string        Get a variable for an environment
  -q, --jq expression     Filter JSON output using a jq expression
      --json fields       Output JSON with the specified fields
  -o, --org string        Get a variable for an organization
  -t, --template string   Format JSON output using a Go template; see "gh help formatting"
  -R, --repo [HOST/]OWNER/REPO   Select another repository using the [HOST/]OWNER/REPO format

## More
- [Details](details.md)
