# Options

## Flags

  -q, --jq expression     Filter JSON output using a jq expression
      --json fields       Output JSON with the specified fields
  -L, --limit int         Maximum number of labels to fetch (default 30)
      --order string      Order of labels returned: {asc|desc} (default "asc")
  -S, --search string     Search label names and descriptions
      --sort string       Sort fetched labels: {created|name} (default "created")
  -t, --template string   Format JSON output using a Go template; see "gh help formatting"
  -w, --web               List labels in the web browser

## Inherited Flags

      --help                     Show help for command
  -R, --repo [HOST/]OWNER/REPO   Select another repository using the [HOST/]OWNER/REPO format
