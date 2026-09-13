# gh repo read-file

Read the contents of a file in a GitHub repository without cloning it.

**Usage:** `gh repo read-file <path> [flags]`

## Options
      --allow-escape-sequences   Allow printing terminal escape sequences
      --clobber                  Overwrite the output path if it already exists
  -q, --jq expression            Filter JSON output using a jq expression
      --json fields              Output JSON with the specified fields
  -o, --output path              Write the file to a path instead of stdout
      --ref string               The branch, tag, or commit to read from
  -R, --repo [HOST/]OWNER/REPO   Select another repository using the [HOST/]OWNER/REPO format
  -t, --template string          Format JSON output using a Go template; see "gh help formatting"

## More
- [Examples](examples.md)
- [Details](details.md)
