List the contents of a directory in a GitHub repository without cloning it.

This command is in preview and subject to change without notice.

By default, the directory is listed from the default branch. Use the `--ref` flag to
list from a specific branch, tag, or commit. When no path is given, the repository root
is listed.

For more information about output formatting flags, see `gh help formatting`.

USAGE
  gh repo read-dir [<path>] [flags]

FLAGS
  -q, --jq expression            Filter JSON output using a jq expression
      --json fields              Output JSON with the specified fields
      --ref string               The branch, tag, or commit to list from
  -R, --repo [HOST/]OWNER/REPO   Select another repository using the [HOST/]OWNER/REPO format
  -t, --template string          Format JSON output using a Go template; see "gh help formatting"

INHERITED FLAGS
  --help   Show help for command

JSON FIELDS
  gitSHA, gitType, mode, modeOctal, name, nameRaw, path, pathRaw, size, submodule,
  type

EXAMPLES
  # List the root of the default branch
  $ gh repo read-dir --repo cli/cli

  # List a subdirectory
  $ gh repo read-dir docs --repo cli/cli

  # List a directory at a specific ref
  $ gh repo read-dir docs --repo cli/cli --ref v2.50.0

  # Print selected fields as JSON
  $ gh repo read-dir docs --repo cli/cli --json name,path,type,size

LEARN MORE
  Use `gh <command> <subcommand> --help` for more information about a command.
  Read the manual at https://cli.github.com/manual
  Learn about exit codes using `gh help exit-codes`
  Learn about accessibility experiences using `gh help accessibility`
