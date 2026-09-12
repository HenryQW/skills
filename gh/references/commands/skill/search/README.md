# gh skill search

Search across all public GitHub repositories for skills matching a keyword.

**Usage:** `gh skill search <query> [flags]`

## Options
  -q, --jq expression     Filter JSON output using a jq expression
      --json fields       Output JSON with the specified fields
  -L, --limit int         Maximum number of results per page (default 15)
      --owner string      Filter results to a specific GitHub user or organization
      --page int          Page number of results to fetch (default 1)
  -t, --template string   Format JSON output using a Go template; see "gh help formatting"

## More
- [Examples](examples.md)
- [Details](details.md)
