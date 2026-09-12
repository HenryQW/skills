# gh variable set

Set a value for a variable on one of the following levels: - repository (default): available to GitHub Actions runs or Dependabot in a repository - environment: available to GitHub Actions runs for a deployment environment in a repository - organization: available to GitHub Actions runs or Dependabot within an organization

**Usage:** `gh variable set <variable-name> [flags]`

## Options
  -b, --body string          The value for the variable (reads from standard input if not specified)
  -e, --env environment      Set deployment environment variable
  -f, --env-file file        Load variable names and values from a dotenv-formatted file
  -o, --org organization     Set organization variable
  -r, --repos repositories   List of repositories that can access an organization variable
  -v, --visibility string    Set visibility for an organization variable: {all|private|selected} (default "private")
  -R, --repo [HOST/]OWNER/REPO   Select another repository using the [HOST/]OWNER/REPO format

## More
- [Examples](examples.md)
- [Details](details.md)
