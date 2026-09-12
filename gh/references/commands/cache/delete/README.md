# gh cache delete

Delete GitHub Actions caches.

**Usage:** `gh cache delete [<cache-id> | <cache-key> | --all] [flags]`

## Options
  -a, --all                          Delete all caches, can be used with --ref to delete all caches for a specific ref
  -r, --ref string                   Delete by cache key and ref, formatted as refs/heads/<branch name> or refs/pull/<number>/merge
      --succeed-on-no-caches --all   Return exit code 0 if no caches found. Must be used in conjunction with --all
  -R, --repo [HOST/]OWNER/REPO   Select another repository using the [HOST/]OWNER/REPO format

## More
- [Examples](examples.md)
- [Details](details.md)
