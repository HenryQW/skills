# Details

## Description

Display the title, body, and other information about a discussion.

To see the comments on a discussion, pass `--comments`. A few latest replies
of each comment will also be retrieved regardless of the selected ordering.

To see the full reply thread of a single comment, pass a comment node ID or
comment URL as the argument instead of a discussion
(e.g., `https://github.com/OWNER/REPO/discussions/123#discussioncomment-456`).

Pagination and ordering can be controlled via `--order`, `--limit`, and `--after` flags.

Use `--web` to open the discussion or comment in a web browser instead.

For more information about output formatting flags, see `gh help formatting`.

## Json Fields

  answerChosenAt, answerChosenBy, answered, author, body, category, closed,
  closedAt, comments, createdAt, id, labels, locked, number, reactionGroups,
  state, stateReason, title, updatedAt, url
