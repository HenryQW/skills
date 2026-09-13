# Details

## Description

Search across all public GitHub repositories for skills matching a keyword.

Uses the GitHub Code Search API to find `SKILL.md` files whose name or
description matches the query term.

Results are ranked by relevance: skills whose name contains the query
term appear first.

Use `--owner` to scope results to a specific GitHub user or organization.

In interactive mode, you can select skills from the results to install directly.

For more information about output formatting flags, see `gh help formatting`.

## Json Fields

  description, namespace, path, repo, skillName, stars
