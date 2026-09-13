# gh codespace ssh

The `ssh` command is used to SSH into a codespace.

**Usage:** `gh codespace ssh [<flags>...] [-- <ssh-flags>...] [<command>]`

## Options
  -c, --codespace string    Name of the codespace
      --config              Write OpenSSH configuration to stdout
  -d, --debug               Log debug data to a file
      --debug-file string   Path of the file log to
      --profile string      Name of the SSH profile to use
  -R, --repo string         Filter codespace selection by repository name (user/repo)
      --repo-owner string   Filter codespace selection by repository owner (username or org)
      --server-port int     SSH server port number (0 => pick unused)

## More
- [Examples](examples.md)
- [Details](details.md)
