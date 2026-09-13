# Details

## Description

Manage comments or replies on a GitHub discussion.

The positional argument can be a discussion number or URL (to add a new
top-level comment), or a comment node ID or comment URL (to reply, edit,
or delete that comment).

When the argument is a discussion number or URL, the default action is to
add a new top-level comment. Likewise, if the argument is a comment URL or ID
the default action is to add a reply.

Use `--edit` to update the comment/reply body, or `--delete` to remove it.

The body can be supplied via `--body`, `--body-file`, or interactively
through an editor.
