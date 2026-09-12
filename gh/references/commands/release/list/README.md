# gh release list

List releases in a repository

**Usage:** `gh release list [flags]`

**Aliases:** `gh release ls`

## Options
      --exclude-drafts         Exclude draft releases
      --exclude-pre-releases   Exclude pre-releases
  -q, --jq expression          Filter JSON output using a jq expression
      --json fields            Output JSON with the specified fields
  -L, --limit int              Maximum number of items to fetch (default 30)
  -O, --order string           Order of releases returned: {asc|desc} (default "desc")
  -t, --template string        Format JSON output using a Go template; see "gh help formatting"
  -R, --repo [HOST/]OWNER/REPO   Select another repository using the [HOST/]OWNER/REPO format

## More
- [Details](details.md)
