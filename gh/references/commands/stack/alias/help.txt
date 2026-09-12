Create a short command alias so you can run "gs [command]" instead of "gh stack [command]".

This installs a small wrapper script into ~/.local/bin/ that forwards all
arguments to "gh stack". The default alias name is "gs", but you can choose
any name by passing it as an argument.

Usage:
  gh stack alias [name] [flags]

Examples:
  # Create the default 'gs' alias
  $ gh stack alias

  # Create a custom alias
  $ gh stack alias gst

  # Remove alias
  $ gh stack alias --remove

Flags:
  -h, --help     help for alias
      --remove   Remove a previously created alias
