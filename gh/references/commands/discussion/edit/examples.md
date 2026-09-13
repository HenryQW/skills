# Examples

  # Edit interactively
  $ gh discussion edit 123

  # Update title, body, and category
  $ gh discussion edit 123 --title "Updated title" --body "Updated body" --category "Ideas"

  # Update body from a file
  $ gh discussion edit 123 --body-file body.md

  # Add and remove labels
  $ gh discussion edit 123 --add-label "bug,help wanted" --remove-label "stale"
