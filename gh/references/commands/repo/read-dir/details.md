# Details

## Description

List the contents of a directory in a GitHub repository without cloning it.

This command is in preview and subject to change without notice.

By default, the directory is listed from the default branch. Use the `--ref` flag to
list from a specific branch, tag, or commit. When no path is given, the repository root
is listed.

For more information about output formatting flags, see `gh help formatting`.

## Json Fields

  gitSHA, gitType, mode, modeOctal, name, nameRaw, path, pathRaw, size, submodule,
  type
