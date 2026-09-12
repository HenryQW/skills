# Details

## Description

Authenticate with a GitHub host.

The default hostname is `github.com`. This can be overridden using the `--hostname`
flag.

The default authentication mode is a web-based browser flow. After completion, an
authentication token will be stored securely in the system credential store.
If a credential store is not found or there is an issue using it gh will fallback
to writing the token to a plain text file. See `gh auth status` for its
stored location.

Alternatively, use `--with-token` to pass in a personal access token (classic) on standard input.
The minimum required scopes for the token are: `repo`, `read:org`, and `gist`.
Take care when passing a fine-grained personal access token to `--with-token`
as the inherent scoping to certain resources may cause confusing behaviour when interacting with other
resources. Favour setting `GH_TOKEN` for fine-grained personal access token usage.

Alternatively, gh will use the authentication token found in environment variables.
This method is most suitable for "headless" use of gh such as in automation. See
`gh help environment` for more info.

To use gh in GitHub Actions, add `GH_TOKEN: ${{ github.token }}` to `env`.

The git protocol to use for git operations on this host can be set with `--git-protocol`,
or during the interactive prompting. Although login is for a single account on a host, setting
the git protocol will take effect for all users on the host.

Specifying `ssh` for the git protocol will detect existing SSH keys to upload,
prompting to create and upload a new key if one is not found. This can be skipped with
`--skip-ssh-key` flag.

For more information on OAuth scopes, see
<https://docs.github.com/en/developers/apps/building-oauth-apps/scopes-for-oauth-apps/>.
