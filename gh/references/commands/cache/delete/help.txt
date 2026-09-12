Delete GitHub Actions caches.

Deletion requires authorization with the `repo` scope.


USAGE
  gh cache delete [<cache-id> | <cache-key> | --all] [flags]

FLAGS
  -a, --all                          Delete all caches, can be used with --ref to delete all caches for a specific ref
  -r, --ref string                   Delete by cache key and ref, formatted as refs/heads/<branch name> or refs/pull/<number>/merge
      --succeed-on-no-caches --all   Return exit code 0 if no caches found. Must be used in conjunction with --all

INHERITED FLAGS
      --help                     Show help for command
  -R, --repo [HOST/]OWNER/REPO   Select another repository using the [HOST/]OWNER/REPO format

EXAMPLES
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

LEARN MORE
  Use `gh <command> <subcommand> --help` for more information about a command.
  Read the manual at https://cli.github.com/manual
  Learn about exit codes using `gh help exit-codes`
  Learn about accessibility experiences using `gh help accessibility`
