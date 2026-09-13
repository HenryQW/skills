# gh cache list

List GitHub Actions caches

**Usage:** `gh cache list [flags]`

**Aliases:** `gh cache ls`

## Options
  -q, --jq expression     Filter JSON output using a jq expression
      --json fields       Output JSON with the specified fields
  -k, --key string        Filter by cache key prefix
  -L, --limit int         Maximum number of caches to fetch (default 30)
  -O, --order string      Order of caches returned: {asc|desc} (default "desc")
  -r, --ref string        Filter by ref, formatted as refs/heads/<branch name> or refs/pull/<number>/merge
  -S, --sort string       Sort fetched caches: {created_at|last_accessed_at|size_in_bytes} (default "last_accessed_at")
  -t, --template string   Format JSON output using a Go template; see "gh help formatting"
  -R, --repo [HOST/]OWNER/REPO   Select another repository using the [HOST/]OWNER/REPO format

## More
- [Examples](examples.md)
- [Details](details.md)
