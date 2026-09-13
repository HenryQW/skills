# gh stack rebase

Pull from remote and do a cascading rebase across the stack.

**Usage:** `gh stack rebase [branch] [flags]`

## Options
      --abort                           Abort rebase and restore all branches
      --committer-date-is-author-date   Set the committer date to the author date during rebase
      --continue                        Continue rebase after resolving conflicts
      --downstack                       Only rebase branches from trunk to current branch
      --no-trunk                        Skip trunk — only rebase stack branches onto each other
      --preserve-dates                  Alias for --committer-date-is-author-date
      --remote string                   Remote to fetch from (defaults to auto-detected remote)
      --upstack                         Only rebase branches from current branch to top

## More
- [Examples](examples.md)
- [Details](details.md)
