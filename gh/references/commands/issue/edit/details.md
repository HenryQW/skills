# Details

## Description

Edit one or more issues within the same repository.

Editing issues' projects requires authorization with the `project` scope.
To authorize, run `gh auth refresh -s project`.

Use `--attach` to upload an image or video to a single issue. Without a body
flag the issue keeps the body it already has and the attachment is appended to it.
If the body references an attached file, such as `![alt](./login.png)`, that
reference is rewritten to point at the uploaded asset instead.
You can attach up to 50 files per command.

Alt text for an image follows the path after `#`, as in
`--attach './login.png#The login error state'`. Without it the filename is used.
A reference already in the body keeps the alt text written there. Video renders
as a player and has no alt text, so it cannot be given any.

If some attachments upload and others fail, the issue is still updated with the
ones that succeeded. The command then exits with a non-zero status, but the edited
issue URLs are still printed to stdout.

The `--add-assignee` and `--remove-assignee` flags both support
the following special values:
- `@me`: assign or unassign yourself
- `@copilot`: assign or unassign Copilot (not supported on GitHub Enterprise Server)
