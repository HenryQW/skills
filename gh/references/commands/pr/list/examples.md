# Examples

  # List PRs authored by you
  $ gh pr list --author "@me"

  # List PRs opened by a GitHub App such as Dependabot
  $ gh pr list --app dependabot

  # List PRs with a specific head branch name
  $ gh pr list --head "typo"

  # List only PRs with all of the given labels
  $ gh pr list --label bug --label "priority 1"

  # Filter PRs using search syntax
  $ gh pr list --search "status:success review:required"

  # Find a PR that introduced a given commit
  $ gh pr list --search "<SHA>" --state merged
