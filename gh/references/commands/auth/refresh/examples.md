# Examples

  # Open a browser to add write:org and read:public_key scopes
  $ gh auth refresh --scopes write:org,read:public_key

  # Open a browser to ensure your authentication credentials have the correct minimum scopes
  $ gh auth refresh

  # Open a browser to idempotently remove the delete_repo scope
  $ gh auth refresh --remove-scopes delete_repo

  # Open a browser to re-authenticate with the default minimum scopes
  $ gh auth refresh --reset-scopes

  # Open a browser to re-authenticate and copy one-time OAuth code to clipboard
  $ gh auth refresh --clipboard
