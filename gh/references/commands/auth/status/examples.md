# Examples

  # Display authentication status for all accounts on all hosts
  $ gh auth status

  # Display authentication status for the active account on a specific host
  $ gh auth status --active --hostname github.example.com

  # Display tokens in plain text
  $ gh auth status --show-token

  # Format authentication status as JSON
  $ gh auth status --json hosts

  # Include plain text token in JSON output
  $ gh auth status --json hosts --show-token

  # Format hosts as a flat JSON array
  $ gh auth status --json hosts --jq '.hosts | add'
