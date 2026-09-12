# Examples

  # Edit the title and body of a pull request
  $ gh pr edit 23 --title "I found a bug" --body "Nothing works"

  # Use a file as the body
  $ gh pr edit 23 --body-file body.txt

  # Append a screenshot to the body, with alt text after "#"
  $ gh pr edit 23 --attach './login.png#The login error state'

  # Append multiple files by repeating the flag
  $ gh pr edit 23 --attach ./before.png --attach ./after.png

  # Manage labels
  $ gh pr edit 23 --add-label "bug,help wanted" --remove-label "core"

  # Manage reviewers
  $ gh pr edit 23 --add-reviewer monalisa,hubot --remove-reviewer myorg/team-name

  # Re-request review
  $ gh pr edit 23 --add-reviewer monalisa

  # Request a review from GitHub Copilot
  $ gh pr edit 23 --add-reviewer "@copilot"

  # Manage assignees
  $ gh pr edit 23 --add-assignee "@me" --remove-assignee monalisa,hubot

  # Assign GitHub Copilot
  $ gh pr edit 23 --add-assignee "@copilot"

  # Manage projects and milestones
  $ gh pr edit 23 --add-project "Roadmap" --remove-project v1,v2
  $ gh pr edit 23 --milestone "Version 1"
  $ gh pr edit 23 --remove-milestone
