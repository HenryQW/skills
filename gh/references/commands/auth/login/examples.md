# Examples

  # Start interactive setup
  $ gh auth login

  # Open a browser to authenticate and copy one-time OAuth code to clipboard
  $ gh auth login --web --clipboard

  # Authenticate against github.com by reading the token from a file
  $ gh auth login --with-token < mytoken.txt

  # Authenticate with specific host
  $ gh auth login --hostname enterprise.internal
