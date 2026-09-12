List GitHub rulesets for a repository or organization.

If no options are provided, the current repository's rulesets are listed. You can query a different
repository's rulesets by using the `--repo` flag. You can also use the `--org` flag to list rulesets
configured for the provided organization.

Use the `--parents` flag to control whether rulesets configured at higher levels that also apply to the provided
repository or organization should be returned. The default is `true`.

Your access token must have the `admin:org` scope to use the `--org` flag, which can be granted by running `gh auth refresh -s admin:org`.


USAGE
  gh ruleset list [flags]

ALIASES
  gh rs ls, gh ruleset ls

FLAGS
  -L, --limit int    Maximum number of rulesets to list (default 30)
  -o, --org string   List organization-wide rulesets for the provided organization
  -p, --parents      Whether to include rulesets configured at higher levels that also apply (default true)
  -w, --web          Open the list of rulesets in the web browser

INHERITED FLAGS
      --help                     Show help for command
  -R, --repo [HOST/]OWNER/REPO   Select another repository using the [HOST/]OWNER/REPO format

EXAMPLES
  # List rulesets in the current repository
  $ gh ruleset list

  # List rulesets in a different repository, including those configured at higher levels
  $ gh ruleset list --repo owner/repo --parents

  # List rulesets in an organization
  $ gh ruleset list --org org-name

LEARN MORE
  Use `gh <command> <subcommand> --help` for more information about a command.
  Read the manual at https://cli.github.com/manual
  Learn about exit codes using `gh help exit-codes`
  Learn about accessibility experiences using `gh help accessibility`
