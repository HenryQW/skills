# gh pr checkout

Check out a pull request in git

**Usage:** `gh pr checkout [<number> | <url> | <branch>] [flags]`

**Aliases:** `gh pr co`

## Options
  -b, --branch string        Local branch name to use (default [the name of the head branch])
      --detach               Checkout PR with a detached HEAD
  -f, --force                Reset the existing local branch to the latest state of the pull request
      --recurse-submodules   Update all submodules after checkout
      --worktree path        Check out the pull request into a worktree at the given path
  -R, --repo [HOST/]OWNER/REPO   Select another repository using the [HOST/]OWNER/REPO format

## More
- [Examples](examples.md)
