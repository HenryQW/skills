# Examples

  $ gh pr create --title "The bug is fixed" --body "Everything works again"
  $ gh pr create --reviewer monalisa,hubot  --reviewer myorg/team-name
  $ gh pr create --project "Roadmap"
  $ gh pr create --base develop --head monalisa:feature
  $ gh pr create --template "pull_request_template.md"
  $ gh pr create --attach './login.png#The login error state'
  $ gh pr create --attach ./before.png --attach ./after.png
