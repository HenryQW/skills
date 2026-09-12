# Options

## Flags

      --app string        Filter by GitHub App author
  -a, --assignee string   Filter by assignee
  -A, --author string     Filter by author (use --app to filter by a GitHub App)
  -B, --base string       Filter by base branch
  -d, --draft             Filter by draft state
  -H, --head string       Filter by head branch ("<owner>:<branch>" syntax not supported)
  -q, --jq expression     Filter JSON output using a jq expression
      --json fields       Output JSON with the specified fields
  -l, --label strings     Filter by label
  -L, --limit int         Maximum number of items to fetch (default 30)
  -S, --search query      Search pull requests with query
  -s, --state string      Filter by state: {open|closed|merged|all} (default "open")
  -t, --template string   Format JSON output using a Go template; see "gh help formatting"
  -w, --web               List pull requests in the web browser

## Inherited Flags

      --help                     Show help for command
  -R, --repo [HOST/]OWNER/REPO   Select another repository using the [HOST/]OWNER/REPO format
