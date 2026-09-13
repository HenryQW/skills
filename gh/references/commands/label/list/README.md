# gh label list

Display labels in a GitHub repository.

**Usage:** `gh label list [flags]`

**Aliases:** `gh label ls`

## Options
  -q, --jq expression     Filter JSON output using a jq expression
      --json fields       Output JSON with the specified fields
  -L, --limit int         Maximum number of labels to fetch (default 30)
      --order string      Order of labels returned: {asc|desc} (default "asc")
  -S, --search string     Search label names and descriptions
      --sort string       Sort fetched labels: {created|name} (default "created")
  -t, --template string   Format JSON output using a Go template; see "gh help formatting"
  -w, --web               List labels in the web browser
  -R, --repo [HOST/]OWNER/REPO   Select another repository using the [HOST/]OWNER/REPO format

## More
- [Examples](examples.md)
- [Details](details.md)
