# Details

## Description

Read the contents of a file in a GitHub repository without cloning it.

This command is in preview and subject to change without notice.

By default, the file is read from the default branch. Use the `--ref` flag to
read from a specific branch, tag, or commit.

When run in TTY mode, the content is shown through your pager. When stdout is piped or
redirected, the raw content is written directly. To save the file to disk instead, use
the `--output` flag.

By default, the command refuses to output a file that contains terminal escape sequences,
since they could manipulate your terminal. Pass `--allow-escape-sequences` to read the file anyway.
This check applies only to terminal and piped output; writing to disk with `--output` always
includes the raw bytes, as if `--allow-escape-sequences` were given.

For more information about output formatting flags, see `gh help formatting`.

## Json Fields

  content, downloadUrl, encoding, gitSHA, gitUrl, htmlUrl, name, path, size, type,
  url
