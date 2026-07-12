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
- `shipyard_manifest` is optional handoff state. Read only its close targets,
  child commits, checks or known skips, and review status.

## Memory boundary

Own memory only for direct invocation; otherwise skip load and distillation and
preserve `.context/decisions.jsonl` for `issue-workbench` or `shipyard`.

## Procedure

1. When this workflow owns memory, invoke `$agent-memory load`; continue on
   `memory_load=SKIPPED` without setup.
2. Resolve `base_branch` from the input or repository default. Prefer its remote-tracking ref when available.
3. Inspect the repo first:
   - `git status --short`
   - `git log --oneline <base_ref>...HEAD`
   - `git diff <base_ref>...HEAD` for the complete committed branch diff.
   - `git diff` for unstaged changes.
   - `git diff --cached` for staged changes.
4. Do not commit `.context/`, `.agents/`, or local progress files.
5. If uncommitted changes are materially unrelated to the intended PR, or the intended scope is ambiguous, stop for user direction. Otherwise commit the focused changes with Conventional Commits.
6. Run the smallest relevant non-destructive validation supported by the repository. When `shipyard_manifest` is present, first resolve the installed Shipyard skill and run `python3 <shipyard_dir>/scripts/manifest.py --manifest <shipyard_manifest> can-reuse $(git rev-parse HEAD)`. Reuse its recorded checks only when that succeeds. If evidence is missing, invalid, or stale, run normal validation and do not present the manifest evidence as current. If no validation applies, record an honest reason in the PR's Testing section.
7. Draft a Conventional Commit-style PR title from the branch commits and complete diff.
8. Push explicitly:
   - Run `git rev-parse --abbrev-ref --symbolic-full-name @{upstream}`.
   - If no upstream exists, run `git push --set-upstream origin HEAD`.
   - Otherwise run `git push`.
9. Draft the PR body from the actual diff and validation. With a manifest, use
   its child issues, final-check close target, checks or known skips, commits,
   and review status; live git remains authoritative.
10. Write multi-line PR body content to a temp file or heredoc.
11. Use `gh` for GitHub or `glab` for GitLab.
12. Create the PR against `base_branch`.
13. If the only non-green health signal is an explicitly waived or replaced
    unavailable external review check, do not invoke repair skills; record
    `Pending external unavailable check: <check>` in caller/progress context.
14. Compact `.context/progress.md`.
15. When this workflow owns memory, invoke `$agent-memory distill` before every
    terminal return, including `Stop` and `Blocked`. `memory_write=SKIPPED` is
    acceptable; on failure, retain the PR URL and record `memory_write=FAILED`
    in caller/progress context.

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
