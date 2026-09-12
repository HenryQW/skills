# Options

## Flags

      --after string             Cursor for the next page of results
      --answered                 Filter by answered state
  -A, --author string            Filter by author
  -c, --category string          Filter by category name or slug
  -q, --jq expression            Filter JSON output using a jq expression
      --json fields              Output JSON with the specified fields
  -l, --label strings            Filter by label
  -L, --limit int                Maximum number of discussions to fetch (default 30)
      --order string             Order of results: {asc|desc} (default "desc")
  -R, --repo [HOST/]OWNER/REPO   Select another repository using the [HOST/]OWNER/REPO format
  -S, --search query             Search discussions with query
      --sort string              Sort by field: {created|updated} (default "updated")
  -s, --state string             Filter by state: {open|closed|all} (default "open")
  -t, --template string          Format JSON output using a Go template; see "gh help formatting"
  -w, --web                      List discussions in the web browser

## Inherited Flags

  --help   Show help for command
