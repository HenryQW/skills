# Details

## Description

Sync destination repository from source repository. Syncing uses the default branch
of the source repository to update the matching branch on the destination
repository so they are equal. A fast forward update will be used except when the
`--force` flag is specified, then the two branches will
be synced using a hard reset.

Without an argument, the local repository is selected as the destination repository.

The source repository is the parent of the destination repository by default.
This can be overridden with the `--source` flag.
