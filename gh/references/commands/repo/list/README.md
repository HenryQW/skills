# gh repo list

List repositories owned by a user or organization.

**Usage:** `gh repo list [<owner>] [flags]`

**Aliases:** `gh repo ls`

## Options
      --archived            Show only archived repositories
      --fork                Show only forks
  -q, --jq expression       Filter JSON output using a jq expression
      --json fields         Output JSON with the specified fields
  -l, --language string     Filter by primary coding language
  -L, --limit int           Maximum number of repositories to list (default 30)
      --no-archived         Omit archived repositories
      --source              Show only non-forks
  -t, --template string     Format JSON output using a Go template; see "gh help formatting"
      --topic strings       Filter by topic
      --visibility string   Filter by repository visibility: {public|private|internal}

## More
- [Details](details.md)
