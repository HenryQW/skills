# Details

## Description

Set a value for a secret on one of the following levels:
- repository (default): available to GitHub Actions runs, Agents sessions, or Dependabot in a repository
- environment: available to GitHub Actions runs for a deployment environment in a repository
- organization: available to GitHub Actions runs, Agents sessions, Dependabot, or Codespaces within an organization
- user: available to Codespaces for your user

Organization and user secrets can optionally be restricted to only be available to
specific repositories.

Secret values are locally encrypted before being sent to GitHub.
