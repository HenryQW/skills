# Examples

  # Add a comment to an issue
  $ gh issue comment 12 --body "Hi from GitHub CLI"

  # Attach a screenshot, with alt text after "#"
  $ gh issue comment 12 --attach './login.png#The login error state'

  # Attach multiple files by repeating the flag
  $ gh issue comment 12 --attach ./before.png --attach ./after.png
