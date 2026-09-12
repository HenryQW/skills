Search for gh extensions.

With no arguments, this command prints out the first 30 extensions
available to install sorted by number of stars. More extensions can
be fetched by specifying a higher limit with the `--limit` flag.

When connected to a terminal, this command prints out three columns.
The first has a ✓ if the extension is already installed locally. The
second is the full name of the extension repository in `OWNER/REPO`
format. The third is the extension's description.

When not connected to a terminal, the ✓ character is rendered as the
word "installed" but otherwise the order and content of the columns
are the same.

This command behaves similarly to `gh search repos` but does not
support as many search qualifiers. For a finer grained search of
extensions, try using:

	gh search repos --topic "gh-extension"

and adding qualifiers as needed. See `gh help search repos` to learn
more about repository search.

For listing just the extensions that are already installed locally,
see:

	gh ext list

For more information about output formatting flags, see `gh help formatting`.

USAGE
  gh extension search [<query>] [flags]

FLAGS
  -q, --jq expression     Filter JSON output using a jq expression
      --json fields       Output JSON with the specified fields
      --license strings   Filter based on license type
  -L, --limit int         Maximum number of extensions to fetch (default 30)
      --order string      Order of repositories returned, ignored unless '--sort' flag is specified: {asc|desc} (default "desc")
      --owner strings     Filter on owner
      --sort string       Sort fetched repositories: {forks|help-wanted-issues|stars|updated} (default "best-match")
  -t, --template string   Format JSON output using a Go template; see "gh help formatting"
  -w, --web               Open the search query in the web browser

INHERITED FLAGS
  --help   Show help for command

JSON FIELDS
  createdAt, defaultBranch, description, forksCount, fullName, hasDownloads,
  hasIssues, hasPages, hasProjects, hasWiki, homepage, id, isArchived, isDisabled,
  isFork, isPrivate, language, license, name, openIssuesCount, owner, pushedAt,
  size, stargazersCount, updatedAt, url, visibility, watchersCount

EXAMPLES
  # List the first 30 extensions sorted by star count, descending
  $ gh ext search

  # List more extensions
  $ gh ext search --limit 300

  # List extensions matching the term "branch"
  $ gh ext search branch

  # List extensions owned by organization "github"
  $ gh ext search --owner github

  # List extensions, sorting by recently updated, ascending
  $ gh ext search --sort updated --order asc

  # List extensions, filtering by license
  $ gh ext search --license MIT

  # Open search results in the browser
  $ gh ext search -w

LEARN MORE
  Use `gh <command> <subcommand> --help` for more information about a command.
  Read the manual at https://cli.github.com/manual
  Learn about exit codes using `gh help exit-codes`
  Learn about accessibility experiences using `gh help accessibility`
