# Options

## Flags

      --app string              Filter by GitHub App author
      --archived                Filter based on the repository archived state {true|false}
      --assignee string         Filter by assignee
      --author string           Filter by author (use --app to filter by a GitHub App)
  -B, --base string             Filter on base branch name
      --checks string           Filter based on status of the checks: {pending|success|failure}
      --closed date             Filter on closed at date
      --commenter user          Filter based on comments by user
      --comments number         Filter on number of comments
      --created date            Filter based on created at date
      --draft                   Filter based on draft state
  -H, --head string             Filter on head branch name
      --interactions number     Filter on number of reactions and comments
      --involves user           Filter based on involvement of user
  -q, --jq expression           Filter JSON output using a jq expression
      --json fields             Output JSON with the specified fields
      --label strings           Filter on label
      --language string         Filter based on the coding language
  -L, --limit int               Maximum number of results to fetch (default 30)
      --locked                  Filter on locked conversation status
      --match strings           Restrict search to specific field of issue: {title|body|comments}
      --mentions user           Filter based on user mentions
      --merged                  Filter based on merged state
      --merged-at date          Filter on merged at date
      --milestone title         Filter by milestone title
      --no-assignee             Filter on missing assignee
      --no-label                Filter on missing label
      --no-milestone            Filter on missing milestone
      --no-project              Filter on missing project
      --order string            Order of results returned, ignored unless '--sort' flag is specified: {asc|desc} (default "desc")
      --owner strings           Filter on repository owner
      --project owner/number    Filter on project board owner/number
      --reactions number        Filter on number of reactions
  -R, --repo OWNER/REPO         Filter on repository, in OWNER/REPO format
      --review string           Filter based on review status: {none|required|approved|changes_requested}
      --review-requested user   Filter on user or team requested to review
      --reviewed-by user        Filter on user who reviewed
      --sort string             Sort fetched results: {comments|reactions|reactions-+1|reactions--1|reactions-smile|reactions-thinking_face|reactions-heart|reactions-tada|interactions|created|updated} (default "best-match")
      --state string            Filter based on state: {open|closed}
      --team-mentions string    Filter based on team mentions
  -t, --template string         Format JSON output using a Go template; see "gh help formatting"
      --updated date            Filter on last updated at date
      --visibility strings      Filter based on repository visibility: {public|private|internal}
  -w, --web                     Open the search query in the web browser

## Inherited Flags

  --help   Show help for command
