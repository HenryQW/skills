# gh codespace cp

The `cp` command copies files between the local and remote file systems.

**Usage:** `gh codespace cp [-e] [-r] [-- [<scp flags>...]] <sources>... <dest>`

## Options
  -c, --codespace string    Name of the codespace
  -e, --expand              Expand remote file names on remote shell
  -p, --profile string      Name of the SSH profile to use
  -r, --recursive           Recursively copy directories
  -R, --repo string         Filter codespace selection by repository name (user/repo)
      --repo-owner string   Filter codespace selection by repository owner (username or org)

## More
- [Examples](examples.md)
- [Details](details.md)
