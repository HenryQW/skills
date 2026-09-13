# Examples

  # Select a gist to edit interactively
  $ gh gist edit

  # Edit a gist file in the default editor
  $ gh gist edit 1234567890abcdef1234567890abcdef

  # Edit a specific file in the gist
  $ gh gist edit 1234567890abcdef1234567890abcdef --filename hello.py

  # Replace a gist file with content from a local file
  $ gh gist edit 1234567890abcdef1234567890abcdef --filename hello.py hello.py

  # Add a new file to the gist
  $ gh gist edit 1234567890abcdef1234567890abcdef --add newfile.py

  # Change the description of the gist
  $ gh gist edit 1234567890abcdef1234567890abcdef --desc "new description"

  # Remove a file from the gist
  $ gh gist edit 1234567890abcdef1234567890abcdef --remove hello.py
