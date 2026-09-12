# Details

## Description

Create a `workflow_dispatch` event for a given workflow.

This command will trigger GitHub Actions to run a given workflow file. The given workflow file must
support an `on.workflow_dispatch` trigger in order to be run in this way.

If the workflow file supports inputs, they can be specified in a few ways:

- Interactively
- Via `-f/--raw-field` or `-F/--field` flags
- As JSON, via standard input

The created workflow run URL will be returned if available.
