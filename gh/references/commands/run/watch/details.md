# Details

## Description

Watch a run until it completes, showing its progress.

By default, all steps are displayed. The `--compact` option can be used to only
show the relevant/failed steps.

This command does not support authenticating via fine grained PATs
as it is not currently possible to create a PAT with the `checks:read` permission.
