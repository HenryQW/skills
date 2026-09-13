# Examples

  # Interactively choose a ruleset to view from all rulesets that apply to the current repository
  $ gh ruleset view

  # Interactively choose a ruleset to view from only rulesets configured in the current repository
  $ gh ruleset view --no-parents

  # View a ruleset configured in the current repository or any of its parents
  $ gh ruleset view 43

  # View a ruleset configured in a different repository or any of its parents
  $ gh ruleset view 23 --repo owner/repo

  # View an organization-level ruleset
  $ gh ruleset view 23 --org my-org
