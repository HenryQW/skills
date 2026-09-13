# gh auth status

Display active account and authentication state on each known GitHub host.

**Usage:** `gh auth status [flags]`

## Options
  -a, --active            Display the active account only
  -h, --hostname string   Check only a specific hostname's auth status
      --jq expression     Filter JSON output using a jq expression
      --json fields       Output JSON with the specified fields
  -t, --show-token        Display the auth token
      --template string   Format JSON output using a Go template; see "gh help formatting"

## More
- [Examples](examples.md)
- [Details](details.md)
