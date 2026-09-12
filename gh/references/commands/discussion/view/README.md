# gh discussion view

Display the title, body, and other information about a discussion.

**Usage:** `gh discussion view {<number> | <discussion-url> | <comment-id> | <comment-url>} [flags]`

## Options
      --after string             Cursor for the next page
  -c, --comments                 View discussion comments
  -q, --jq expression            Filter JSON output using a jq expression
      --json fields              Output JSON with the specified fields
  -L, --limit int                Maximum number of comments or replies to fetch (default 30)
      --order string             Order of comments or replies: {oldest|newest} (default "newest")
  -R, --repo [HOST/]OWNER/REPO   Select another repository using the [HOST/]OWNER/REPO format
  -t, --template string          Format JSON output using a Go template; see "gh help formatting"
  -w, --web                      Open a discussion in the browser

## More
- [Examples](examples.md)
- [Details](details.md)
