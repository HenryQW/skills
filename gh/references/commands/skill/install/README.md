# gh skill install

Install agent skills from a GitHub repository or local directory into your local environment.

**Usage:** `gh skill install <repository> [<skill[@version]>] [flags]`

**Aliases:** `gh skill add, gh skills add`

## Options
      --agent string        Target agent (see supported values above)
      --all                 Install all skills without prompting for skill selection
      --allow-hidden-dirs   Include skills in hidden directories (e.g. .claude/skills/, .agents/skills/)
      --dir string          Install to a custom directory (overrides --agent and --scope)
  -f, --force               Overwrite existing skills without prompting
      --from-local          Treat the argument as a local directory path instead of a repository
      --pin string          Pin to a specific git tag or commit SHA
      --scope string        Installation scope: {project|user} (default "project")
      --upstream            Install from the upstream source when a re-published skill is detected

## More
- [Examples](examples.md)
- [Details](details.md)
