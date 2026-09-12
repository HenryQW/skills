# gh agent-task view

View an agent task session.

**Usage:** `gh agent-task view [<session-id> | <pr-number> | <pr-url> | <pr-branch>] [flags]`

## Options
      --follow                   Follow agent session logs
  -q, --jq expression            Filter JSON output using a jq expression
      --json fields              Output JSON with the specified fields
      --log                      Show agent session logs
  -R, --repo [HOST/]OWNER/REPO   Select another repository using the [HOST/]OWNER/REPO format
  -t, --template string          Format JSON output using a Go template; see "gh help formatting"
  -w, --web                      Open agent task in the browser

## More
- [Examples](examples.md)
- [Details](details.md)
