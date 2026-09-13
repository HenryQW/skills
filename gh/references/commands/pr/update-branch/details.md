# Details

## Description

Update a pull request branch with latest changes of the base branch.

Without an argument, the pull request that belongs to the current branch is selected.

The default behavior is to update with a merge commit (i.e., merging the base branch
into the PR's branch). To reconcile the changes with rebasing on top of the base
branch, the `--rebase` option should be provided.
