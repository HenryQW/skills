# Examples

  $ gh issue create --title "I found a bug" --body "Nothing works"
  $ gh issue create --attach './login.png#The login error state'
  $ gh issue create --attach ./before.png --attach ./after.png
  $ gh issue create --label "bug,help wanted"
  $ gh issue create --label bug --label "help wanted"
  $ gh issue create --assignee monalisa,hubot
  $ gh issue create --assignee "@me"
  $ gh issue create --assignee "@copilot"
  $ gh issue create --project "Roadmap"
  $ gh issue create --template "Bug Report"
  $ gh issue create --type Bug
  $ gh issue create --parent 100
  $ gh issue create --parent https://github.com/cli/go-gh/issues/42
  $ gh issue create --blocked-by 200,201 --blocking 300
