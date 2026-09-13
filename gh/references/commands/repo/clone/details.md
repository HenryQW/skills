# Details

## Description

Clone a GitHub repository locally. Pass additional `git clone` flags by listing
them after `--`.

If the `OWNER/` portion of the `OWNER/REPO` repository argument is omitted, it
defaults to the name of the authenticating user.

When a protocol scheme is not provided in the repository argument, the `git_protocol` will be
chosen from your configuration, which can be checked via `gh config get git_protocol`. If the protocol
scheme is provided, the repository will be cloned using the specified protocol.

If the repository is a fork, its parent repository will be added as an additional
git remote called `upstream`. The remote name can be configured using `--upstream-remote-name`.
The `--upstream-remote-name` option supports an `@owner` value which will name
the remote after the owner of the parent repository.

If the repository is a fork, its parent repository will be set as the default remote repository.
To skip this behavior, use `--no-upstream`.
