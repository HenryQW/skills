# Examples

  # Select a codespace from a list of all codespaces you own
  $ gh cs view

  # View the details of a specific codespace
  $ gh cs view -c codespace-name-12345

  # View the list of all available fields for a codespace
  $ gh cs view --json

  # View specific fields for a codespace
  $ gh cs view --json displayName,machineDisplayName,state
