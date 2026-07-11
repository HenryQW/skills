---
name: pr-launchpad
description: Create or publish a GitHub or GitLab pull request when asked to open or create a PR. Use when must inspect the actual diff, commit pending work with Conventional Commits, push the current branch, and create a PR with a Conventional Commit title and fixed body template.
---

# pr-launchpad

Create a PR from the current branch.

## Inputs

- `base_branch` is optional and defaults to the repository default branch.
- `issue_number` is optional and can be derived from the branch name or PR title.
- `issue_numbers` is optional when one PR resolves multiple issues.
- `shipyard_manifest` is optional. When provided, read it for close targets, child commits, testing bullets, known skips, and prior review status.

## Memory boundary

Own the memory boundary only when the user invoked `pr-launchpad` directly. When called by `issue-workbench` or `shipyard`, skip memory load and distillation; preserve `.context/decisions.jsonl` for the caller.

## Procedure

1. If this workflow owns the memory boundary, invoke `$agent-memory load`. Continue when it returns `memory_load=SKIPPED`; do not run setup.
2. Resolve `base_branch` from the input or repository default. Prefer its remote-tracking ref when available.
3. Inspect the repo first:
   - `git status --short`
   - `git log --oneline <base_ref>...HEAD`
   - `git diff <base_ref>...HEAD` for the complete committed branch diff.
   - `git diff` for unstaged changes.
   - `git diff --cached` for staged changes.
4. Do not commit `.context/`, `.agents/`, or local progress files.
5. If uncommitted changes are materially unrelated to the intended PR, or the intended scope is ambiguous, stop for user direction. Otherwise commit the focused changes with Conventional Commits.
6. Run the smallest relevant non-destructive validation supported by the repository. If none applies, record an honest reason in the PR's Testing section.
7. Draft a Conventional Commit-style PR title from the branch commits and complete diff.
8. Push explicitly:
   - Run `git rev-parse --abbrev-ref --symbolic-full-name @{upstream}`.
   - If no upstream exists, run `git push --set-upstream origin HEAD`.
   - Otherwise run `git push`.
9. Draft the PR body from the actual diff and validation results.
   - If `shipyard_manifest` is present, use its merged child issues, `final_check`, checks, known skips, child commits, and review gate status for the PR body.
   - Still inspect live git before creating the PR; the manifest is handoff state, not a replacement for repository state.
10. Write multi-line PR body content to a temp file or heredoc.
11. Use `gh` for GitHub or `glab` for GitLab.
12. Create the PR against `base_branch`.
13. If PR health is inspected after creation and the only non-green signal is a known unavailable external review check that the user or caller explicitly waived or replaced, do not invoke repair skills; record `Pending external unavailable check: <check>` in caller/progress context while preserving the final user reply as only the PR URL.
14. Compact `.context/progress.md`.
15. If this workflow owns the memory boundary, invoke `$agent-memory distill` as the final guard before every terminal return, including early `Stop` and `Blocked` results. `memory_write=SKIPPED` is acceptable. If distillation fails, do not hide the PR URL; report `memory_write=FAILED` to the caller/progress context.

Always use this PR body template:

```markdown
## Summary

- <2 to 4 bullets covering the main changes>

## Testing

- <commands actually run>
- <or an honest reason no relevant validation was run>

## Close Issue

- Closes #<issue_number>
```

Use one `Closes #...` bullet for each issue the PR clearly resolves; otherwise omit the section.

Finish by replying with only the PR URL.
