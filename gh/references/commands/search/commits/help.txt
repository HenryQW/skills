Search for commits on GitHub.

The command supports constructing queries using the GitHub search syntax,
using the parameter and qualifier flags, or a combination of the two.

GitHub search syntax is documented at:
<https://docs.github.com/search-github/searching-on-github/searching-commits>

For more information on handling search queries containing a hyphen, run `gh search --help`.

For more information about output formatting flags, see `gh help formatting`.

USAGE
  gh search commits [<query>] [flags]

FLAGS
      --author string            Filter by author
      --author-date date         Filter based on authored date
      --author-email string      Filter on author email
      --author-name string       Filter on author name
      --committer string         Filter by committer
      --committer-date date      Filter based on committed date
      --committer-email string   Filter on committer email
      --committer-name string    Filter on committer name
      --hash string              Filter by commit hash
  -q, --jq expression            Filter JSON output using a jq expression
      --json fields              Output JSON with the specified fields
  -L, --limit int                Maximum number of commits to fetch (default 30)
      --merge                    Filter on merge commits
      --order string             Order of commits returned, ignored unless '--sort' flag is specified: {asc|desc} (default "desc")
      --owner strings            Filter on repository owner
      --parent string            Filter by parent hash
  -R, --repo OWNER/REPO          Filter on repository, in OWNER/REPO format
      --sort string              Sort fetched commits: {author-date|committer-date} (default "best-match")
  -t, --template string          Format JSON output using a Go template; see "gh help formatting"
      --tree string              Filter by tree hash
      --visibility strings       Filter based on repository visibility: {public|private|internal}
  -w, --web                      Open the search query in the web browser

INHERITED FLAGS
  --help   Show help for command

JSON FIELDS
  author, commit, committer, id, parents, repository, sha, url

EXAMPLES
  # Search commits matching set of keywords "readme" and "typo"
  $ gh search commits readme typo

  # Search commits matching phrase "bug fix"
  $ gh search commits "bug fix"

  # Search commits using raw search qualifiers as separate arguments
  $ gh search commits fix author:monalisa merge:false

  # Search commits committed by user "monalisa"
  $ gh search commits --committer=monalisa

  # Search commits authored by users with name "Jane Doe"
  $ gh search commits --author-name="Jane Doe"

  # Search commits matching hash "8dd03144ffdc6c0d486d6b705f9c7fba871ee7c3"
  $ gh search commits --hash=8dd03144ffdc6c0d486d6b705f9c7fba871ee7c3

  # Search commits authored before February 1st, 2022
  $ gh search commits --author-date="<2022-02-01"

LEARN MORE
  Use `gh <command> <subcommand> --help` for more information about a command.
  Read the manual at https://cli.github.com/manual
  Learn about exit codes using `gh help exit-codes`
  Learn about accessibility experiences using `gh help accessibility`
