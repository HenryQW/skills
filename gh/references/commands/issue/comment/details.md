# Details

## Description

Add a comment to a GitHub issue.

Without body text or attachments supplied through flags, the command will
interactively prompt for the comment text.

Use `--attach` to upload an image or video. If the body already references an
attached file, such as `![alt](./login.png)`, that reference is rewritten to point
at the uploaded asset. Any attached file the body does not reference is appended
to the end of the comment.
You can attach up to 50 files per command.

Alt text for an image follows the path after `#`, as in
`--attach './login.png#The login error state'`. Without it the filename is used.
A reference already in the body keeps the alt text written there. Video renders
as a player and has no alt text, so it cannot be given any.
