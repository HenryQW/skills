---
name: fix-ci-failures
description: Take a GitHub or GitLab review request from failing CI to green or clearly improved CI by inspecting failures, applying minimal fixes, verifying narrowly, committing, and pushing.
---

# Fix CI Failures

Use when a review request has failing CI and the user wants it fixed, improved, committed, and pushed.

## Checklist

1. Inspect repository state.
   - Run `git status --short --branch`.
   - Identify the current branch.
   - Detect the forge from `git remote -v`.
   - Use `gh` for GitHub and `glab` for GitLab.
   - Inspect the current review request before choosing commit messages, titles, bodies, or replies.

2. Inspect failing CI before editing.
   - GitHub: start with `gh pr checks`; use `gh run view <run-id>` and `gh run view <run-id> --log-failed` when logs are needed.
   - GitLab: start with `glab ci status`; use `glab pipeline view` and job logs when logs are needed.
   - Identify the failing job, failing step, and concrete error.
   - Do not edit code before identifying the likely root cause.

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

7. Use noninteractive forge operations.
   - Do not open editors.
   - For multi-line review request content, write the body to a temp file or heredoc and pass that file to `gh` or `glab`.
   - If a command fails, resolve the issue and retry when reasonable.
   - Stop only for missing credentials, missing permissions, or unsafe repository state.

8. Final response.
   - Include failing check.
   - Include root cause.
   - Include fix.
   - Include verification actually run.
   - Include commit hash or commit summary.
   - Include push result.
   - Include any remaining CI uncertainty.
