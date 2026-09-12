# gh repo read-dir

List the contents of a directory in a GitHub repository without cloning it.

**Usage:** `gh repo read-dir [<path>] [flags]`

## Options
  -q, --jq expression            Filter JSON output using a jq expression
      --json fields              Output JSON with the specified fields
      --ref string               The branch, tag, or commit to list from
  -R, --repo [HOST/]OWNER/REPO   Select another repository using the [HOST/]OWNER/REPO format
  -t, --template string          Format JSON output using a Go template; see "gh help formatting"

## More
- [Examples](examples.md)
- [Details](details.md)
