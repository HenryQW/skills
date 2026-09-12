# Details

## Description

Create an issue on GitHub.

Use `--attach` to upload an image or video. The attachment is appended to the
body. If the body references an attached file, such as `![alt](./login.png)`, that
reference is rewritten to point at the uploaded asset instead.
You can attach up to 50 files per command.

Alt text for an image follows the path after `#`, as in
`--attach './login.png#The login error state'`. Without it the filename is used.
A reference already in the body keeps the alt text written there. Video renders
as a player and has no alt text, so it cannot be given any.

If some attachments upload and others fail, the issue is still created with the
ones that succeeded. The command then exits with a non-zero status, but the new
issue's URL is still printed to stdout.

Adding an issue to projects requires authorization with the `project` scope.
To authorize, run `gh auth refresh -s project`.

The `--assignee` flag supports the following special values:
- `@me`: assign yourself
- `@copilot`: assign Copilot (not supported on GitHub Enterprise Server)
