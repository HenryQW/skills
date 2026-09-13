# Examples

  # See diff for current branch
  $ gh pr diff

  # See diff for a specific PR
  $ gh pr diff 123

  # Exclude files from diff output
  $ gh pr diff --exclude '*.yml' --exclude 'generated/*'

  # Exclude matching files by name
  $ gh pr diff --name-only --exclude '*.generated.*'
