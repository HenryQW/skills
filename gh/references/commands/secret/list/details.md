# Details

## Description

List secrets on one of the following levels:
- repository (default): available to GitHub Actions runs, Agents sessions, or Dependabot in a repository
- environment: available to GitHub Actions runs for a deployment environment in a repository
- organization: available to GitHub Actions runs, Agents sessions, Dependabot, or Codespaces within an organization
- user: available to Codespaces for your user

For more information about output formatting flags, see `gh help formatting`.

## Json Fields

  name, numSelectedRepos, selectedReposURL, updatedAt, visibility
