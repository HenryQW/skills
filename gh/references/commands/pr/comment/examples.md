# Examples

  # Add a comment to a pull request
  $ gh pr comment 13 --body "Hi from GitHub CLI"

  # Attach a screenshot, with alt text after "#"
  $ gh pr comment 13 --attach './login.png#The login error state'

  # Attach multiple files by repeating the flag
  $ gh pr comment 13 --attach ./before.png --attach ./after.png
