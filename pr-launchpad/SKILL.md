---
name: pr-launchpad
description: Create or publish a GitHub or GitLab pull request when asked to open or create a PR. Use when Codex must inspect the actual diff, commit pending work with Conventional Commits, push the current branch, and create a PR with a Conventional Commit title and fixed body template.
---

# pr-launchpad

Create a PR from the current branch.

## Inputs

- `base_branch` is optional and defaults to the repository default branch.
- `issue_number` is optional and can be derived from the branch name or PR title.
- `issue_numbers` is optional when one PR resolves multiple issues.

## Procedure

1. Inspect the repo first:
   - `git status --short`
   - `git diff --stat`
   - Relevant `git diff` commands for changed files.
2. Do not commit `.context/`, `.agents/`, or local progress files.
3. If changes are uncommitted, split unrelated work into focused commits.
4. Use Conventional Commits for new commits.
5. PR title must be Conventional Commit style, derived from branch commits and the actual diff.
6. Push explicitly:
   - Run `git rev-parse --abbrev-ref --symbolic-full-name @{upstream}`.
   - If no upstream exists, run `git push --set-upstream origin HEAD`.
   - Otherwise run `git push`.
7. Draft the PR title and body from the actual diff.
8. Write multi-line PR body content to a temp file or heredoc.
9. Use `gh` for GitHub or `glab` for GitLab.
10. Create the PR against `base_branch`.
11. Compact `.context/progress.md`.

Always use this PR body template:

```markdown
## Summary

- <2 to 4 bullets covering the main changes>

## Testing

- <commands actually run>
- <or "Not run (not requested)">

## Close Issue

- Closes #<issue_number>
```

Use one `Closes #...` bullet for each issue the PR clearly resolves; otherwise omit the section.

Finish by replying with only the PR URL.
