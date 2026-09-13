# Examples

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
