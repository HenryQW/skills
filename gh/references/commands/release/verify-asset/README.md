# gh release verify-asset

Verify that a given asset file originated from a specific GitHub Release using cryptographically signed attestations.

**Usage:** `gh release verify-asset [<tag>] <file-path> [flags]`

## Options
      --format string     Output format: {json}
  -q, --jq expression     Filter JSON output using a jq expression
  -t, --template string   Format JSON output using a Go template; see "gh help formatting"
  -R, --repo [HOST/]OWNER/REPO   Select another repository using the [HOST/]OWNER/REPO format

## More
- [Examples](examples.md)
- [Details](details.md)
