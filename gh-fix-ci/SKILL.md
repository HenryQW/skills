---
name: gh-fix-ci
description: "Fix GitHub PR CI failures and review feedback end-to-end using gh: inspect failures and threads, apply minimal fixes, verify narrowly, commit, push, reply, and resolve."
---

# GitHub Fix CI

Use when a GitHub PR or review request has failing CI, unresolved review comments, requested changes, or similar PR cleanup work.

## Checklist

1. Inspect repository and PR state.
   - Run `git status --short --branch`.
   - Identify the current branch.
   - Confirm GitHub remote context with `git remote -v`.
   - Run `gh auth status`; stop for credentials if it fails.
   - Inspect the current PR before choosing commit messages, titles, bodies, or replies.

```sh
gh auth status
gh pr view --json number,url,headRefName,baseRefName,title,body,reviewDecision,headRepositoryOwner,headRepository
```

2. Inspect failing CI before editing.
   - Start with PR checks.
   - Identify the failing check, job, step, and concrete error.
   - Use failed run logs before editing.
   - Do not edit code until the likely root cause is identified.

```sh
PR="<number>"
gh pr checks "$PR" --json name,state,bucket,link,workflow,startedAt,completedAt
gh run view "<run-id>" --json databaseId,status,conclusion,url,workflowName,jobs
gh run view "<run-id>" --log-failed
gh run view --job "<job-id>" --log-failed
```

3. Inspect unresolved review threads when review feedback is in scope.
   - Use thread-aware GraphQL or an existing repo helper.
   - Do not treat flat PR comments as complete thread state.
   - Ignore resolved threads unless the user asks to audit them.
   - If paginated results continue, fetch all pages before classifying.

4. Classify each failing check or unresolved thread.
   - `actionable`: concrete code, test, dependency, config, docs, or CI fix.
   - `non-actionable`: already fixed, outdated, duplicate, incorrect, or out of scope.
   - `ambiguous`: needs clarification or cannot be safely resolved.

5. Apply the minimal fix.
   - Map the error or comment to the smallest required change.
   - Prefer repository conventions and existing templates.
   - Avoid opportunistic refactors.
   - Split unrelated changes into separate commits.

6. Verify narrowly.
   - Run the smallest command that proves or de-risks the fix.
   - Prefer the exact failing test, linter, typecheck, build step, or package command.
   - Record the command and result.
   - If local verification is impossible, state why and use the closest available check.

7. Commit only required changes.
   - Review `git diff` before committing.
   - Stage only intended files.
   - Use Conventional Commits: `type(scope): summary` or `type: summary`.
   - Allowed types: `feat`, `fix`, `chore`, `docs`, `refactor`, `test`, `perf`, `build`, `ci`, `style`.

8. Push explicitly.
   - Always run `git rev-parse --abbrev-ref --symbolic-full-name @{upstream}`.
   - If it fails, run `git push --set-upstream origin HEAD`.
   - Otherwise run `git push`.

```sh
git diff
git add <intended-files>
git commit -m "fix(scope): summary"
git rev-parse --abbrev-ref --symbolic-full-name @{upstream}
git push --set-upstream origin HEAD  # only if upstream is missing
git push                             # only if upstream exists
git rev-parse --short HEAD
```

9. Reply and resolve review threads when applicable.
   - Do not open editors.
   - Use temp files or heredocs for multi-line bodies.
   - Reply before resolving a thread.
   - Resolve only threads fixed by the pushed commit or resolved with explicit rationale.
   - Re-fetch thread state until selected unresolved threads are closed or blocked.

```sh
BODY_FILE="$(mktemp)"
cat > "$BODY_FILE" <<'EOF'
<reply body>
EOF
gh api graphql -F threadId="$THREAD_ID" -F body=@"$BODY_FILE" -f query='
mutation($threadId:ID!, $body:String!) {
  addPullRequestReviewThreadReply(input:{pullRequestReviewThreadId:$threadId, body:$body}) {
    comment { id url }
  }
}'
rm -f "$BODY_FILE"

gh api graphql -F threadId="$THREAD_ID" -f query='
mutation($threadId:ID!) {
  resolveReviewThread(input:{threadId:$threadId}) {
    thread { id isResolved }
  }
}'
```

10. Final response.
   - Include PR URL or number.
   - Include failing check and root cause, if CI was involved.
   - Include reviewed threads and outcome, if review comments were involved.
   - Include fix.
   - Include verification actually run.
   - Include commit hash or commit summary.
   - Include push result.
   - Include remaining CI uncertainty or unresolved blockers.

## Write Policy

Default to committing, pushing, replying, and resolving when those actions are needed. Stop only for missing credentials, missing permissions, conflicting requirements, or unsafe repository state.
