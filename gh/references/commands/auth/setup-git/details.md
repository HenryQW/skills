# Details

## Description

This command configures `git` to use GitHub CLI as a credential helper.
For more information on git credential helpers please reference:
<https://git-scm.com/docs/gitcredentials>.

By default, GitHub CLI will be set as the credential helper for all authenticated hosts.
If there is no authenticated hosts the command fails with an error.

Alternatively, use the `--hostname` flag to specify a single host to be configured.
If the host is not authenticated with, the command fails with an error.
