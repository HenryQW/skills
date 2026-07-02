---
name: fix-ci-failures
description: Take a GitHub review request from failing CI to green or clearly improved CI using gh, minimal fixes, narrow verification, focused commits, and explicit pushes.
---

# Fix CI Failures

Use when a GitHub review request has failing CI and the user wants it fixed, improved, committed, and pushed.

## Checklist

1. Inspect repository state.
   - Run `git status --short --branch`.
   - Identify the current branch.
   - Confirm GitHub remote context with `git remote -v`.
   - Use `gh`; if `gh auth status` fails, stop for credentials.
   - Inspect the current PR before choosing commit messages, titles, bodies, or replies.

```bash
gh auth status
gh pr view --json number,url,headRefName,baseRefName,title,body,reviewDecision
```

2. Inspect failing CI before editing.
   - Start with PR checks; inspect the failed run logs before editing.
   - Identify the failing job, failing step, and concrete error.
   - Do not edit code before identifying the likely root cause.

```bash
PR="<number>"
gh pr checks "$PR" --json name,state,bucket,link,workflow
gh run view "<run-id>" --json databaseId,status,conclusion,url,workflowName,jobs
gh run view "<run-id>" --log-failed
gh run view --job "<job-id>" --log-failed
```

3. Determine the minimal fix.
   - Map the error to the smallest code, test, dependency, config, or CI change that addresses it.
   - Prefer repository conventions and existing templates.
   - Avoid opportunistic refactors.
   - Split unrelated changes into separate commits.

4. Verify narrowly.
   - Run the smallest command that proves or de-risks the fix.
   - Prefer the exact failing test, linter, typecheck, build step, or package-level command.
   - Record the command actually run and the result.
   - If local verification is impossible, state why and use the closest available check.

5. Commit only required changes.
   - Review `git diff` before committing.
   - Stage only intended files.
   - Use Conventional Commits only.
   - Allowed formats: `type(scope): summary` or `type: summary`.
   - Allowed types: `feat`, `fix`, `chore`, `docs`, `refactor`, `test`, `perf`, `build`, `ci`, `style`.
   - Keep each commit focused.

6. Push explicitly.
   - Always run `git rev-parse --abbrev-ref --symbolic-full-name @{upstream}`.
   - If it fails, run `git push --set-upstream origin HEAD`.
   - Otherwise run `git push`.

7. Use noninteractive GitHub operations.
   - Do not open editors.
   - For multi-line PR comments or review bodies, write a temp file or heredoc and pass it to `gh`.
   - If a command fails, resolve the issue and retry when reasonable.
   - Stop only for missing credentials, missing permissions, or unsafe repository state.

```bash
BODY_FILE="$(mktemp)"
cat > "$BODY_FILE" <<'EOF'
<body>
EOF
gh pr comment "$PR" --body-file "$BODY_FILE"
rm -f "$BODY_FILE"
```

## Commit And Push Example

```bash
git diff
git add <intended-files>
git commit -m "fix(scope): summary"
git rev-parse --abbrev-ref --symbolic-full-name @{upstream}
# If the upstream command failed:
git push --set-upstream origin HEAD
# Otherwise:
git push
git rev-parse --short HEAD
```

8. Final response.
   - Include failing check.
   - Include root cause.
   - Include fix.
   - Include verification actually run.
   - Include commit hash or commit summary.
   - Include push result.
   - Include any remaining CI uncertainty.
