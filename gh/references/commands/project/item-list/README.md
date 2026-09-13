# gh project item-list

List the items in a project.

**Usage:** `gh project item-list [<number>] [flags]`

## Options
      --field stringArray      Name of a field to show as an extra column
      --field-id stringArray   ID of a field to show as an extra column
      --format string          Output format: {json}
  -q, --jq expression          Filter JSON output using a jq expression
  -L, --limit int              Maximum number of items to fetch (default 30)
      --owner string           Login of the owner. Use "@me" for the current user
      --query string           Filter items using the Projects filter syntax, e.g. "assignee:octocat -status:Done"
  -t, --template string        Format JSON output using a Go template; see "gh help formatting"

## More
- [Examples](examples.md)
- [Details](details.md)
