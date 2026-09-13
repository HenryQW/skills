# Examples

  # View all rules that apply to the current branch
  $ gh ruleset check

  # View all rules that apply to a branch named "my-branch" in a different repository
  $ gh ruleset check my-branch --repo owner/repo

  # View all rules that apply to the default branch in a different repository
  $ gh ruleset check --default --repo owner/repo

  # View a ruleset configured in a different repository or any of its parents
  $ gh ruleset view 23 --repo owner/repo

  # View an organization-level ruleset
  $ gh ruleset view 23 --org my-org
