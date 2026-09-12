# gh workflow run

Create a `workflow_dispatch` event for a given workflow.

**Usage:** `gh workflow run [<workflow-id> | <workflow-name>] [flags]`

## Options
  -F, --field key=value       Add a string parameter in key=value format, respecting @ syntax (see "gh help api").
      --json                  Read workflow inputs as JSON via STDIN
  -f, --raw-field key=value   Add a string parameter in key=value format
  -r, --ref string            Branch or tag name which contains the version of the workflow file you'd like to run
  -R, --repo [HOST/]OWNER/REPO   Select another repository using the [HOST/]OWNER/REPO format

## More
- [Examples](examples.md)
- [Details](details.md)
