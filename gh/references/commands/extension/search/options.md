# Options

## Flags

  -q, --jq expression     Filter JSON output using a jq expression
      --json fields       Output JSON with the specified fields
      --license strings   Filter based on license type
  -L, --limit int         Maximum number of extensions to fetch (default 30)
      --order string      Order of repositories returned, ignored unless '--sort' flag is specified: {asc|desc} (default "desc")
      --owner strings     Filter on owner
      --sort string       Sort fetched repositories: {forks|help-wanted-issues|stars|updated} (default "best-match")
  -t, --template string   Format JSON output using a Go template; see "gh help formatting"
  -w, --web               Open the search query in the web browser

## Inherited Flags

  --help   Show help for command
