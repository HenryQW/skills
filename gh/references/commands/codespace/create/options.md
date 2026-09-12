# Options

## Flags

  -b, --branch string               Repository branch
      --default-permissions         Do not prompt to accept additional permissions requested by the codespace
      --devcontainer-path string    Path to the devcontainer.json file to use when creating codespace
  -d, --display-name string         Display name for the codespace (48 characters or less)
      --idle-timeout duration       Allowed inactivity before codespace is stopped, e.g. "10m", "1h"
  -l, --location string             Location: {EastUs|SouthEastAsia|WestEurope|WestUs2} (determined automatically if not provided)
  -m, --machine string              Hardware specifications for the VM
  -R, --repo string                 Repository name with owner: user/repo
      --retention-period duration   Allowed time after shutting down before the codespace is automatically deleted (maximum 30 days), e.g. "1h", "72h"
  -s, --status                      Show status of post-create command and dotfiles
  -w, --web                         Create codespace from browser, cannot be used with --display-name, --idle-timeout, or --retention-period

## Inherited Flags

  --help   Show help for command
