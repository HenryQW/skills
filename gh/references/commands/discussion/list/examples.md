# Examples

  # List open discussions
  $ gh discussion list

  # List discussions with a specific category
  $ gh discussion list --category General

  # List closed discussions by author
  $ gh discussion list --state closed --author monalisa

  # List all discussions (closed or open) by label
  $ gh discussion list --state all --label bug,enhancement

  # List answered Q&A discussions as JSON
  $ gh discussion list --answered --json number,title,url

  # List unanswered Q&A discussions as JSON
  $ gh discussion list --answered=false --json number,title,url
