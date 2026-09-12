# Details

## Description

Display active account and authentication state on each known GitHub host.

For each host, the authentication state of each known account is tested and any issues are included in the output.
Each host section will indicate the active account, which will be used when targeting that host.

If an account on any host (or only the one given via `--hostname`) has authentication issues,
the command will exit with 1 and output to stderr. Note that when using the `--json` option, the command
will always exit with zero regardless of any authentication issues, unless there is a fatal error.

To change the active account for a host, see `gh auth switch`.

For more information about output formatting flags, see `gh help formatting`.

## Json Fields

  hosts
