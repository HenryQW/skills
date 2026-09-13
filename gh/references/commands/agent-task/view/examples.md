# Examples

  # View an agent task by session ID
  $ gh agent-task view e2fa49d2-f164-4a56-ab99-498090b8fcdf

  # View an agent task by pull request number in current repo
  $ gh agent-task view 12345

  # View an agent task by pull request number
  $ gh agent-task view --repo OWNER/REPO 12345

  # View an agent task by pull request reference
  $ gh agent-task view OWNER/REPO#12345

  # View a pull request agents tasks in the browser
  $ gh agent-task view 12345 --web
