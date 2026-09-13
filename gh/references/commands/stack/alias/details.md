# Details

## Description

Create a short command alias so you can run "gs [command]" instead of "gh stack [command]".

This installs a small wrapper script into ~/.local/bin/ that forwards all
arguments to "gh stack". The default alias name is "gs", but you can choose
any name by passing it as an argument.
