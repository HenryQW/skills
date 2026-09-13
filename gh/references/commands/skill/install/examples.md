# Examples

  # Interactive: choose repo, skill, and agent
  $ gh skill install

  # Choose a skill from the repo interactively
  $ gh skill install github/awesome-copilot

  # List available skills non-interactively (e.g. to pipe into grep)
  $ gh skill install github/awesome-copilot | grep review

  # Install a specific skill
  $ gh skill install github/awesome-copilot git-commit

  # Install all skills from a repository
  $ gh skill install github/awesome-copilot --all

  # Install a specific version
  $ gh skill install github/awesome-copilot git-commit@v1.2.0

  # Install from a large namespaced repo by path (efficient, skips full discovery)
  $ gh skill install github/awesome-copilot skills/monalisa/code-review

  # Install from a non-standard nested path (efficient, skips full discovery)
  $ gh skill install monalisa/skills-repo packages/agent-skills/code-review

  # Install from a local directory
  $ gh skill install ./my-skills-repo --from-local

  # Install a specific local skill
  $ gh skill install ./my-skills-repo git-commit --from-local

  # Install for Claude Code at user scope
  $ gh skill install github/awesome-copilot git-commit --agent claude-code --scope user

  # Pin to a specific git ref
  $ gh skill install github/awesome-copilot git-commit --pin v2.0.0

  # Install skills from hidden directories (e.g. .claude/skills/)
  $ gh skill install owner/repo --allow-hidden-dirs
