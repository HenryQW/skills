# Details

## Description

Merge a pull request on GitHub.

Without an argument, the pull request that belongs to the current branch
is selected.

When targeting a branch that requires a merge queue, no merge strategy is required.
If required checks have not yet passed, auto-merge will be enabled.
If required checks have passed, the pull request will be added to the merge queue.
To bypass a merge queue and merge directly, pass the `--admin` flag.
