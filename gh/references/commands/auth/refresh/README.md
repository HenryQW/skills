Expand or fix the permission scopes for stored credentials for active account.

The `--scopes` flag accepts a comma separated list of scopes you want
your gh credentials to have. If no scopes are provided, the command
maintains previously added scopes.

The `--remove-scopes` flag accepts a comma separated list of scopes you
want to remove from your gh credentials. Scope removal is idempotent.
The minimum set of scopes (`repo`, `read:org`, and `gist`) cannot be removed.

The `--reset-scopes` flag resets the scopes for your gh credentials to
the default set of scopes for your auth flow.

If you have multiple accounts in `gh auth status` and want to refresh the credentials for an
inactive account, you will have to use `gh auth switch` to that account first before using
this command, and then switch back when you are done.

For more information on OAuth scopes, see
<https://docs.github.com/en/developers/apps/building-oauth-apps/scopes-for-oauth-apps/>.


USAGE
  gh auth refresh [flags]

FLAGS
  -c, --clipboard               Copy one-time OAuth device code to clipboard
  -h, --hostname string         The GitHub host to use for authentication
      --insecure-storage        Save authentication credentials in plain text instead of credential store
  -r, --remove-scopes strings   Authentication scopes to remove from gh
      --reset-scopes            Reset authentication scopes to the default minimum set of scopes
  -s, --scopes strings          Additional authentication scopes for gh to have

INHERITED FLAGS
  --help   Show help for command

EXAMPLES
  # Open a browser to add write:org and read:public_key scopes
  $ gh auth refresh --scopes write:org,read:public_key

  # Open a browser to ensure your authentication credentials have the correct minimum scopes
  $ gh auth refresh

  # Open a browser to idempotently remove the delete_repo scope
  $ gh auth refresh --remove-scopes delete_repo

  # Open a browser to re-authenticate with the default minimum scopes
  $ gh auth refresh --reset-scopes

  # Open a browser to re-authenticate and copy one-time OAuth code to clipboard
  $ gh auth refresh --clipboard

LEARN MORE
  Use `gh <command> <subcommand> --help` for more information about a command.
  Read the manual at https://cli.github.com/manual
  Learn about exit codes using `gh help exit-codes`
  Learn about accessibility experiences using `gh help accessibility`
