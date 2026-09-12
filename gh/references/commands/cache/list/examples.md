# Examples

  # List caches for current repository
  $ gh cache list

  # List caches for specific repository
  $ gh cache list --repo cli/cli

  # List caches sorted by least recently accessed
  $ gh cache list --sort last_accessed_at --order asc

  # List caches that have keys matching a prefix (or that match exactly)
  $ gh cache list --key key-prefix

  # List caches for a specific branch, replace <branch-name> with the actual branch name
  $ gh cache list --ref refs/heads/<branch-name>

  # List caches for a specific pull request, replace <pr-number> with the actual pull request number
  $ gh cache list --ref refs/pull/<pr-number>/merge
