# Details

## Description

Define a word that will expand to a full gh command when invoked.

The expansion may specify additional arguments and flags. If the expansion includes
positional placeholders such as `$1`, extra arguments that follow the alias will be
inserted appropriately. Otherwise, extra arguments will be appended to the expanded
command.

Use `-` as expansion argument to read the expansion string from standard input. This
is useful to avoid quoting issues when defining expansions.

If the expansion starts with `!` or if `--shell` was given, the expansion is a shell
expression that will be evaluated through the `sh` interpreter when the alias is
invoked. This allows for chaining multiple commands via piping and redirection.
