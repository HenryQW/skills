# Details

## Description

View changes in a pull request.

Without an argument, the pull request that belongs to the current branch
is selected.

With `--web` flag, open the pull request diff in a web browser instead.

Use `--exclude` to filter out files matching a glob pattern. The pattern
uses forward slashes as path separators on all platforms. You can repeat
the flag to exclude multiple patterns.

By default, terminal escape sequences in the diff are neutralized, since
they could manipulate your terminal. Pass `--allow-escape-sequences` to
print the diff verbatim, for example when piping a patch to another program.
