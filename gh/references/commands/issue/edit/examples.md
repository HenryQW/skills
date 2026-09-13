# Examples

  $ gh issue edit 23 --title "I found a bug" --body "Nothing works"
  $ gh issue edit 23 --add-label "bug,help wanted" --remove-label "core"
  $ gh issue edit 23 --add-assignee "@me" --remove-assignee monalisa,hubot
  $ gh issue edit 23 --add-assignee "@copilot"
  $ gh issue edit 23 --add-project "Roadmap" --remove-project v1,v2
  $ gh issue edit 23 --milestone "Version 1"
  $ gh issue edit 23 --remove-milestone
  $ gh issue edit 23 --body-file body.txt
  $ gh issue edit 23 --attach './login.png#The login error state'
  $ gh issue edit 23 --attach ./before.png --attach ./after.png
  $ gh issue edit 23 34 --add-label "help wanted"
  $ gh issue edit 23 --type Bug
  $ gh issue edit 23 --remove-type
  $ gh issue edit 23 --parent 100
  $ gh issue edit 23 --remove-parent
  $ gh issue edit 100 --add-sub-issue 123,124
  $ gh issue edit 123 --add-blocked-by 200 --add-blocking 300,301
