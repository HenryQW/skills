# gh stack merge

Merge some or all of a stack of pull requests using GitHub's atomic stack merge.

**Usage:** `gh stack merge [<stack-number> | <pr-number>] [flags]`

## Options
      --merge                 Merge with a merge commit
      --merge-method string   Merge method to use: merge, squash, or rebase
      --rebase                Rebase and merge
      --squash                Squash and merge
  -y, --yes                   Merge without prompting for confirmation

## More
- [Examples](examples.md)
- [Details](details.md)
