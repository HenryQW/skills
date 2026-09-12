# gh variable list

List variables on one of the following levels: - repository (default): available to GitHub Actions runs or Dependabot in a repository - environment: available to GitHub Actions runs for a deployment environment in a repository - organization: available to GitHub Actions runs or Dependabot within an organization

**Usage:** `gh variable list [flags]`

**Aliases:** `gh variable ls`

## Options
  -e, --env string        List variables for an environment
  -q, --jq expression     Filter JSON output using a jq expression
      --json fields       Output JSON with the specified fields
  -o, --org string        List variables for an organization
  -t, --template string   Format JSON output using a Go template; see "gh help formatting"
  -R, --repo [HOST/]OWNER/REPO   Select another repository using the [HOST/]OWNER/REPO format

## More
- [Details](details.md)
