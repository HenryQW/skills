# Details

## Description

Show CI status for a single pull request.

Without an argument, the pull request that belongs to the current branch
is selected.

When the `--json` flag is used, it includes a `bucket` field, which categorizes
the `state` field into `pass`, `fail`, `pending`, `skipping`, or `cancel`.

Additional exit codes:
	8: Checks pending

For more information about output formatting flags, see `gh help formatting`.

## Json Fields

  bucket, completedAt, description, event, link, name, startedAt, state, workflow
