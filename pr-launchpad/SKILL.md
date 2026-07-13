---
name: pr-launchpad
description: Create or publish a GitHub or GitLab pull request when asked to open or create a PR. Use when must inspect the actual diff, commit pending work with Conventional Commits, push the current branch, and create a PR with a Conventional Commit title and fixed body template.
---

# pr-launchpad

Publish the current branch as a pull request.

## Inputs and Memory

- `base_branch` defaults to the repository default branch.
- `issue_number` or `issue_numbers` may come from input, branch, or title.
- `shipyard_manifest` supplies only close targets, child commits, checks/skips,
  and review status.

Direct invocation owns `$agent-memory load` and distillation; nested invocation
preserves `.context/decisions.jsonl` for `issue-workbench` or `shipyard`.

## Procedure

1. Load memory when owned; `memory_load=SKIPPED` continues without setup.
2. Resolve the base, preferring its remote-tracking ref. Inspect `git status
   --short`, `git log --oneline <base>...HEAD`, the committed branch diff, and
   staged and unstaged diffs. Do not commit `.context/`, `.agents/`, or local
   progress. Stop when unrelated changes make intended scope ambiguous;
   otherwise make the focused Conventional Commit.
3. Run the smallest relevant non-destructive validation. With a manifest, first
   run `python3 <shipyard_dir>/scripts/manifest.py --manifest
   <shipyard_manifest> can-reuse $(git rev-parse HEAD)` and reuse recorded
   evidence only on success. Otherwise validate normally; state honestly when
   no relevant check exists.
4. Derive a Conventional Commit PR title and the fixed body below from the live
   diff and validation. Manifest evidence never overrides git.
5. Check `git rev-parse --abbrev-ref --symbolic-full-name @{upstream}`. Push with
   `git push --set-upstream origin HEAD` when absent, otherwise `git push`.
6. Write the multiline body to a temporary file or heredoc, then create against
   the base with `gh` or `glab`. An explicitly waived or replaced unavailable
   external review check is recorded as `Pending external unavailable check:
   <check>` in caller/progress context, not routed to repair skills.
7. Compact `.context/progress.md`. When memory is owned, distill before every
   terminal return; failure retains the PR URL and records `memory_write=FAILED`.

```markdown
## Summary

- <2 to 4 bullets covering the main changes>

## Testing

- <commands actually run or an honest reason none applied>

## Close Issue

- Closes #<issue_number>
```

Use one closure bullet per clearly resolved issue; otherwise omit the section.
Reply with only the PR URL.
