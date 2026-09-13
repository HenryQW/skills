# Details

## Description

Delete a GitHub repository.

With no argument, deletes the current repository. Otherwise, deletes the specified repository.

For safety, when no repository argument is provided, the `--yes` flag is ignored
and you will be prompted for confirmation. To delete the current repository non-interactively,
specify it explicitly (e.g., `gh repo delete owner/repo --yes`).

Deletion requires authorization with the `delete_repo` scope.
To authorize, run `gh auth refresh -s delete_repo`
