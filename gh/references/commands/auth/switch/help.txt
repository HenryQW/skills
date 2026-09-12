Switch the active account for a GitHub host.

This command changes the authentication configuration that will
be used when running commands targeting the specified GitHub host.

If the specified host has two accounts, the active account will be switched
automatically. If there are more than two accounts, disambiguation will be
required either through the `--user` flag or an interactive prompt.

For a list of authenticated accounts you can run `gh auth status`.


USAGE
  gh auth switch [flags]

FLAGS
  -h, --hostname string   The hostname of the GitHub instance to switch account for
  -u, --user string       The account to switch to

INHERITED FLAGS
  --help   Show help for command

EXAMPLES
  # Select what host and account to switch to via a prompt
  $ gh auth switch

  # Switch the active account on a specific host to a specific user
  $ gh auth switch --hostname enterprise.internal --user monalisa

LEARN MORE
  Use `gh <command> <subcommand> --help` for more information about a command.
  Read the manual at https://cli.github.com/manual
  Learn about exit codes using `gh help exit-codes`
  Learn about accessibility experiences using `gh help accessibility`
