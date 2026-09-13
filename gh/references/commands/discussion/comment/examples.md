# Examples

  # Add a top-level comment to discussion #123
  $ gh discussion comment 123 --body 'Thanks'

  # Reply to a comment using its URL
  $ gh discussion comment 'https://github.com/OWNER/REPO/discussions/123#discussioncomment-456' --body 'Thanks'

  # Reply to a comment using its node ID
  $ gh discussion comment DC_abc123 --body 'Thanks'

  # Edit a comment/reply
  $ gh discussion comment 'https://github.com/OWNER/REPO/discussions/123#discussioncomment-456' --edit --body 'Thanks'

  # Delete a comment/reply
  $ gh discussion comment 'https://github.com/OWNER/REPO/discussions/123#discussioncomment-456' --delete

  # Delete a comment/reply without confirmation prompt
  $ gh discussion comment 'https://github.com/OWNER/REPO/discussions/123#discussioncomment-456' --delete --yes
