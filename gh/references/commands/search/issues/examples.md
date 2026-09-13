# Examples

  # Search issues matching set of keywords "readme" and "typo"
  $ gh search issues readme typo

  # Search issues matching phrase "broken feature"
  $ gh search issues "broken feature"

  # Search issues using raw search qualifiers as separate arguments
  $ gh search issues label:bug author:monalisa state:open

  # Search issues and pull requests in cli organization
  $ gh search issues --include-prs --owner=cli

  # Search open issues assigned to yourself
  $ gh search issues --assignee=@me --state=open

  # Search issues with numerous comments
  $ gh search issues --comments=">100"

  # Search issues without label "bug"
  $ gh search issues -- -label:bug

  # Search issues only from un-archived repositories (default is all repositories)
  $ gh search issues --owner github --archived=false

  # Search issues using semantic (natural-language) ranking
  $ gh search issues "feature broken on web" --search-type semantic

  # Search issues using hybrid (keyword + semantic) ranking
  $ gh search issues "feature broken" --search-type hybrid
