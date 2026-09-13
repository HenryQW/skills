# Examples

  # Search pull requests matching set of keywords "fix" and "bug"
  $ gh search prs fix bug

  # Search draft pull requests in cli repository
  $ gh search prs --repo=cli/cli --draft

  # Search pull requests using raw search qualifiers as separate arguments
  $ gh search prs is:merged author:monalisa

  # Search open pull requests requesting your review
  $ gh search prs --review-requested=@me --state=open

  # Search merged pull requests assigned to yourself
  $ gh search prs --assignee=@me --merged

  # Search pull requests with numerous reactions
  $ gh search prs --reactions=">100"

  # Search pull requests without label "bug"
  $ gh search prs -- -label:bug

  # Search pull requests only from un-archived repositories (default is all repositories)
  $ gh search prs --owner github --archived=false
