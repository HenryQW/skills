# gh auth login

Authenticate with a GitHub host.

**Usage:** `gh auth login [flags]`

## Options
  -c, --clipboard             Copy one-time OAuth device code to clipboard
  -p, --git-protocol string   The protocol to use for git operations on this host: {ssh|https}
  -h, --hostname string       The hostname of the GitHub instance to authenticate with
      --insecure-storage      Save authentication credentials in plain text instead of credential store
  -s, --scopes strings        Additional authentication scopes to request
      --skip-ssh-key          Skip generate/upload SSH key prompt
  -w, --web                   Open a browser to authenticate
      --with-token            Read token from standard input

## More
- [Examples](examples.md)
- [Details](details.md)
