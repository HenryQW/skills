# gh pr diff

View changes in a pull request.

**Usage:** `gh pr diff [<number> | <url> | <branch>] [flags]`

## Options
      --allow-escape-sequences   Allow printing terminal escape sequences
      --color string             Use color in diff output: {always|never|auto} (default "auto")
  -e, --exclude patterns         Exclude files matching glob patterns from the diff
      --name-only                Display only names of changed files
      --patch                    Display diff in patch format
  -w, --web                      Open the pull request diff in the browser
  -R, --repo [HOST/]OWNER/REPO   Select another repository using the [HOST/]OWNER/REPO format

## More
- [Examples](examples.md)
- [Details](details.md)
