---
name: gh-fix-ci
description: "Fix GitHub PR CI failures using gh: inspect failed checks/logs, identify root cause, apply minimal fix, verify narrowly, commit, and push."
---

# GitHub Fix CI

Use when the current GitHub PR has failing CI or needs CI-related cleanup.

## Procedure

1. Inspect repo and PR state.

```sh
git status --short --branch
git remote -v
gh auth status
PR="$(gh pr view --json number --jq .number)"
BRANCH="$(git branch --show-current)"
gh pr view "$PR" --json number,url,headRefName,baseRefName,title,body,reviewDecision,statusCheckRollup
```

2. Inspect failing checks before editing.

```sh
gh pr checks "$PR" --json name,state,bucket,workflow,link,startedAt,completedAt
gh pr checks "$PR" --json name,bucket,workflow,link --jq '.[] | select(.bucket=="fail")'
```

Identify the failing check, job or provider, failing step, and concrete error before changing files.

If the failed check links to GitHub Actions, inspect the run logs.

```sh
RUN_ID="$(gh pr checks "$PR" --json bucket,link --jq '.[] | select(.bucket=="fail") | .link | capture("/actions/runs/(?<id>[0-9]+)")?.id' | head -n1)"
test -n "$RUN_ID" && gh run view "$RUN_ID" --json databaseId,status,conclusion,url,workflowName,jobs
test -n "$RUN_ID" && gh run view "$RUN_ID" --log-failed
```

If no GitHub Actions run id is available, inspect the check link or provider output available from the CLI, then continue with the same root-cause workflow.

3. Determine the minimal fix.

- Map the failure to the smallest code, test, dependency, config, or CI change.
- Prefer repository conventions and existing templates.
- Do not refactor opportunistically.
- Split unrelated fixes into separate commits.

4. Verify narrowly.

Run the smallest command that proves or de-risks the fix.

Prefer the exact failing test, linter, typecheck, build step, or package-level command.

Record the command and result.

5. Commit only required changes.

```sh
git diff
git diff --check
git status --short
git add <intended-files>
git commit -m "fix(scope): summary"
```

Use Conventional Commits only.

Allowed formats: `type(scope): summary` or `type: summary`.

Allowed types: `feat`, `fix`, `chore`, `docs`, `refactor`, `test`, `perf`, `build`, `ci`, `style`.

6. Push explicitly.

```sh
if git rev-parse --abbrev-ref --symbolic-full-name '@{upstream}' >/dev/null 2>&1; then
  git push
else
  git push --set-upstream origin HEAD
fi
git rev-parse --short HEAD
```

7. Final response.

Include:

- PR URL or number.
- Failing check.
- Root cause.
- Fix.
- Verification actually run.
- Push result.
- Remaining CI uncertainty, if any.

## Policy

Do not edit before identifying the likely root cause.

Do not open editors.

Use temp files or heredocs for any multi-line forge content.

If a command fails, resolve the issue and retry when reasonable.

Stop only for missing credentials, missing permissions, conflicting requirements, or unsafe repository state.
