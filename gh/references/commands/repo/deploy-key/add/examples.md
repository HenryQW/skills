# Examples

  # Generate a passwordless SSH key and add it as a deploy key to a repository
  $ ssh-keygen -t ed25519 -C "my description" -N "" -f ~/.ssh/gh-test
  $ gh repo deploy-key add ~/.ssh/gh-test.pub
