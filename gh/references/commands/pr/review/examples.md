# Examples

  # Approve the pull request of the current branch
  $ gh pr review --approve

  # Leave a review comment for the current branch
  $ gh pr review --comment -b "interesting"

  # Add a review for a specific pull request
  $ gh pr review 123

  # Request changes on a specific pull request
  $ gh pr review 123 -r -b "needs more ASCII art"
