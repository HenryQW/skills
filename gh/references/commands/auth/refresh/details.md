# Details

## Description

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
