# Examples

  # Delete a cache by id
  $ gh cache delete 1234

  # Delete a cache by key
  $ gh cache delete cache-key

  # Delete a cache by id in a specific repo
  $ gh cache delete 1234 --repo cli/cli

  # Delete a cache by key and branch ref
  $ gh cache delete cache-key --ref refs/heads/feature-branch

  # Delete a cache by key and PR ref
  $ gh cache delete cache-key --ref refs/pull/<PR-number>/merge

  # Delete all caches (exit code 1 on no caches)
  $ gh cache delete --all

  # Delete all caches for a specific ref
  $ gh cache delete --all --ref refs/pull/<PR-number>/merge

  # Delete all caches (exit code 0 on no caches)
  $ gh cache delete --all --succeed-on-no-caches
