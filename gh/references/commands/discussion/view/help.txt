Display the title, body, and other information about a discussion.

To see the comments on a discussion, pass `--comments`. A few latest replies
of each comment will also be retrieved regardless of the selected ordering.

To see the full reply thread of a single comment, pass a comment node ID or
comment URL as the argument instead of a discussion
(e.g., `https://github.com/OWNER/REPO/discussions/123#discussioncomment-456`).

Pagination and ordering can be controlled via `--order`, `--limit`, and `--after` flags.

Use `--web` to open the discussion or comment in a web browser instead.

For more information about output formatting flags, see `gh help formatting`.

USAGE
  gh discussion view {<number> | <discussion-url> | <comment-id> | <comment-url>} [flags]

FLAGS
      --after string             Cursor for the next page
  -c, --comments                 View discussion comments
  -q, --jq expression            Filter JSON output using a jq expression
      --json fields              Output JSON with the specified fields
  -L, --limit int                Maximum number of comments or replies to fetch (default 30)
      --order string             Order of comments or replies: {oldest|newest} (default "newest")
  -R, --repo [HOST/]OWNER/REPO   Select another repository using the [HOST/]OWNER/REPO format
  -t, --template string          Format JSON output using a Go template; see "gh help formatting"
  -w, --web                      Open a discussion in the browser

INHERITED FLAGS
  --help   Show help for command

JSON FIELDS
  answerChosenAt, answerChosenBy, answered, author, body, category, closed,
  closedAt, comments, createdAt, id, labels, locked, number, reactionGroups,
  state, stateReason, title, updatedAt, url

EXAMPLES
  # View a discussion by number
  $ gh discussion view 123

  # View a discussion by URL
  $ gh discussion view https://github.com/OWNER/REPO/discussions/123

  # View with comments
  $ gh discussion view 123 --comments

  # View with oldest comments first
  $ gh discussion view 123 --comments --order oldest

  # Limit to 10 comments
  $ gh discussion view 123 --comments --limit 10

  # Fetch the next page of comments
  $ gh discussion view 123 --comments --after CURSOR

  # View the reply thread of a comment by node ID
  $ gh discussion view DC_abc123

  # View the reply thread of a comment by URL
  $ gh discussion view 'https://github.com/OWNER/REPO/discussions/123#discussioncomment-456'

  # Paginate through replies
  $ gh discussion view DC_abc123 --limit 10 --after CURSOR

  # Open in browser
  $ gh discussion view 123 --web

LEARN MORE
  Use `gh <command> <subcommand> --help` for more information about a command.
  Read the manual at https://cli.github.com/manual
  Learn about exit codes using `gh help exit-codes`
  Learn about accessibility experiences using `gh help accessibility`
