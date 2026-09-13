# Details

## Description

Edit a draft issue or a project item.

The usual way to select the item and field is by name: pass the project
`number` plus `--owner`, point at the item with its issue or pull
request `--url`, and name the field with `--field`. For single-select
fields, `--value` is the option name.

For scripts and machine use, you can also pass GraphQL node IDs directly with
`--id`, `--field-id` and `--project-id` (and, for single-select
fields, `--single-select-option-id`).

Note that `--url` is the issue or pull request URL, not a project URL, so its
owner may differ from the project's; `--owner` selects the project.

For non-draft issues, only a single field value can be updated per invocation.

Remove a project item field value with `--clear`.

For more information about output formatting flags, see `gh help formatting`.
