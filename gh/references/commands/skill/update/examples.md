# Examples

  # Check and update all skills interactively
  $ gh skill update

  # Update specific skills
  $ gh skill update mcp-cli git-commit

  # Update all without prompting
  $ gh skill update --all

  # Re-download all skills (restore locally modified files)
  $ gh skill update --force --all

  # Check for updates without applying (read-only)
  $ gh skill update --dry-run

  # Unpin skills and update them to latest
  $ gh skill update --unpin
