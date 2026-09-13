# Details

## Description

Runs the GitHub Copilot CLI.

Executing the Copilot CLI through `gh` is currently in preview and subject to change.

If already installed, `gh` will execute the Copilot CLI found in your `PATH`.
If the Copilot CLI is not installed, it will be downloaded to /Users/henry/.local/share/gh/copilot.

Use `--remove` to remove the downloaded Copilot CLI.

This command is only supported on Windows, Linux, and Darwin, on amd64/x64
or arm64 architectures.

To prevent `gh` from interpreting flags intended for Copilot,
use `--` before Copilot flags and args.

Learn more at https://gh.io/copilot-cli
