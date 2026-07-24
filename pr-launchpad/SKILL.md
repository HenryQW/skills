---
name: pr-launchpad
description: Create or publish a GitHub or GitLab pull request when asked to open or create a PR. Use when must inspect the actual diff, commit pending work with Conventional Commits, push the current branch, and create a PR with a Conventional Commit title and fixed body template.
---

# pr-launchpad

Publish the current branch as a pull request.

## Inputs and Memory

- `base_branch` defaults to the repository default branch.
- `issue_number` or `issue_numbers` may come from input, branch, or title.
- `validated_head` plus non-empty `validation` commands/results may come from nested `issue-workbench`.
- `shipyard_manifest` supplies only close targets, child heads, checks/skips,
  and review status.

Direct invocation owns `$agent-memory`; nested invocation defers it to
`issue-workbench` or `shipyard`.

## Procedure

1. Resolve the base, preferring its remote-tracking ref. Inspect `git status
   --short`, `git log --oneline <base>...HEAD`, the committed branch diff, and
   staged and unstaged diffs. Do not commit `.context/`, `.agents/`, or local
   progress. Stop when unrelated changes make intended scope ambiguous;
   otherwise make the focused Conventional Commit.
2. Reuse HEAD-bound validation before running a check. With a manifest, first
   run `python3 <shipyard_dir>/scripts/manifest.py --manifest
   <shipyard_manifest> can-reuse $(git rev-parse HEAD)` and reuse recorded
   evidence only on success. Without a manifest, reuse nested Workbench evidence
   only when `validated_head` equals current `HEAD` and validation is non-empty.
   Otherwise run the smallest relevant non-destructive validation; state
   honestly when no relevant check exists.
3. Derive a Conventional Commit PR title and the fixed body below from the live
   diff and validation. Manifest evidence never overrides git.
4. Resolve the upstream and its SHA. Push with `git push --set-upstream origin
   HEAD` when absent, `git push` when its SHA differs from `HEAD`, and do not
   push when they already match.
5. Write the multiline body to a temporary file or heredoc. Before creating,
   query open PRs/MRs whose source is the current branch (`gh pr list --head
   <branch>` or the `glab` equivalent). Reuse exactly one only when its source
   branch, resolved base, and issue/diff scope match; refresh its title/body to
   the fixed values when needed. If multiple candidates exist, or a same-branch
   request has a different base or scope, stop instead of creating a duplicate.
   Otherwise create against the resolved base.
6. After create or reuse, when `shipyard_manifest` is present, require:

   ```bash
   python3 <shipyard_dir>/scripts/manifest.py --manifest <shipyard_manifest> set-pr <url>
   ```

   An explicitly waived or replaced unavailable external review check is
   recorded as `Pending external unavailable check: <check>` in caller/progress
   context, not routed to repair skills.
7. Compact `.context/progress.md` without suppressing a created or reused PR URL.

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
