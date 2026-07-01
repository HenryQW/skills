---
name: gh-fix-ci
description: Fix actionable GitHub PR review comments or CI feedback end-to-end. Use when Codex must inspect unresolved review threads or failing checks, implement actionable fixes, commit and push those fixes, resolve fixed threads, and reply to non-actionable threads.
---

# GitHub Fix CI And Review Comments

Use this skill when the user asks to fix GitHub PR feedback, CI failures, unresolved review comments, requested changes, or a similar PR cleanup queue where GitHub write-back is expected.

Treat the durable workflow as:

`inspect all unresolved threads -> fix actionable -> commit + explicit push -> reply directly to every selected thread -> resolve replied threads`

## 1) Resolve PR Context

- If the user provides a repository and PR number or URL, use that directly.
- If the request is about the current branch PR, use local git context plus `gh auth status` and `gh pr view --json number,url,headRefName,baseRefName`.
- If CLI authentication fails, ask the user to refresh `gh` auth before making GitHub writes.
- Inspect repository instructions, PR templates, and existing commit style before choosing commit messages, PR replies, or verification scope.

## 2) Fetch Source Of Truth

- Fetch thread-aware review data with GraphQL or an existing repository script that returns `reviewThreads`, `isResolved`, `isOutdated`, file anchors, line anchors, and comment bodies.
- Fetch failing checks with `gh pr checks` and, when needed, inspect failing GitHub Actions logs before editing.
- Do not treat flat PR comments as complete review-thread state.
- Inspect every unresolved review thread in the selected scope before editing, replying, or resolving so code changes, rationale-only replies, and commit boundaries are chosen from the full request state.
- Ignore already-resolved review threads unless the user asks to audit them.

Use the command recipes below instead of inventing new `gh` calls when they fit.

## Known Working `gh` Commands

Set these variables before running the recipes:

```bash
OWNER="<owner>"
REPO="<repo>"
PR="<number>"
BRANCH="<head-branch>"
```

Resolve current-branch PR context:

```bash
gh auth status
gh pr view --json number,url,headRefName,baseRefName,headRepositoryOwner,headRepository
```

Fetch unresolved review threads with stable GraphQL fields. Use pagination or an equivalent repository helper; do not proceed from only the first page when more review threads exist.

```bash
gh api graphql --paginate \
  -F owner="$OWNER" \
  -F name="$REPO" \
  -F number="$PR" \
  -f query='
query($owner:String!, $name:String!, $number:Int!, $endCursor:String) {
  repository(owner:$owner, name:$name) {
    pullRequest(number:$number) {
      id
      number
      url
      reviewThreads(first:100, after:$endCursor) {
        pageInfo { hasNextPage endCursor }
        nodes {
          id
          isResolved
          isOutdated
          viewerCanReply
          viewerCanResolve
          path
          line
          originalLine
          startLine
          originalStartLine
          comments(first:100) {
            pageInfo { hasNextPage endCursor }
            nodes {
              id
              author { login }
              body
              createdAt
              url
            }
          }
        }
      }
    }
  }
}'
```

If any thread has more than 100 comments, fetch the remaining comments for that thread before classifying it.

Reply to a review thread:

```bash
BODY_FILE="$(mktemp)"
cat > "$BODY_FILE" <<'EOF'
<reply body>
EOF
gh api graphql \
  -F threadId="$THREAD_ID" \
  -F body=@"$BODY_FILE" \
  -f query='
mutation($threadId:ID!, $body:String!) {
  addPullRequestReviewThreadReply(input:{
    pullRequestReviewThreadId:$threadId,
    body:$body
  }) {
    comment { id url }
  }
}'
rm -f "$BODY_FILE"
```

Resolve a review thread:

```bash
gh api graphql \
  -F threadId="$THREAD_ID" \
  -f query='
mutation($threadId:ID!) {
  resolveReviewThread(input:{threadId:$threadId}) {
    thread { id isResolved }
  }
}'
```

Inspect PR checks and failing Actions logs:

```bash
gh pr checks "$PR" --json name,state,bucket,link,workflow,startedAt,completedAt
gh pr checks "$PR" --required --json name,state,bucket,link,workflow
gh run view "$RUN_ID" --json databaseId,status,conclusion,url,workflowName,jobs
gh run view "$RUN_ID" --log-failed
gh run view --job "$JOB_ID" --log-failed
```

Commit and push the current branch:

```bash
git status --short
git add <intended-files>
git commit -m "<type>(<scope>): <summary>"
if git rev-parse --abbrev-ref --symbolic-full-name '@{upstream}' >/dev/null 2>&1; then
  git push
else
  git push --set-upstream origin HEAD
fi
git rev-parse HEAD
```

Use `--repo "$OWNER/$REPO"` on `gh pr ...` and `gh run ...` commands when the current working directory is not the target repository.

## 3) Classify Feedback

For each unresolved thread or failing check, classify it as:

- `actionable`: a concrete code, test, config, docs, or CI fix is needed.
- `non-actionable`: already fixed by current code, outdated, incorrect, duplicate, conflicting with a stronger requirement, or impossible without changing the requested scope.
- `ambiguous`: not enough information to safely act.

If the user says to fix all feedback, proceed with all unresolved actionable items. For ambiguous items, either clarify with the user or leave a specific GitHub reply explaining the blocker when the user's directive is to clear every thread.

## 4) Fix Actionable Items

- Keep each change traceable to the review thread or failing check it addresses.
- Preserve unrelated user changes and do not bundle opportunistic cleanup.
- Add or update focused tests when the fix changes behavior.
- Run verification appropriate to the touched code and the failing checks.
- If verification cannot run, record the exact blocker and include it in the PR reply or final summary.

## 5) Commit And Push

If files changed:

- Inspect the diff and stage only the intended files.
- Split unrelated fix sets into separate commits; keep each commit focused on the threads or checks it resolves.
- Commit with scoped Conventional Commit messages.
- Push explicitly: check upstream with `git rev-parse --abbrev-ref --symbolic-full-name @{upstream}`. If no upstream is configured, run `git push --set-upstream origin HEAD`; otherwise run `git push`.
- Record the pushed commit SHA for later replies.

Do not resolve fixed review threads before the commit is pushed unless the user explicitly directs otherwise.

## 6) Resolve Threads

Resolve threads after the pushed commit when code changed. If no files changed because every selected thread is non-actionable, reply and resolve those non-actionable threads immediately after classification.

- For each actionable thread fixed by the commit, reply with a short note that names the fix and, when useful, the commit SHA or verification run.
- Resolve that review thread.
- For each non-actionable thread, reply with the concrete reason it is not actionable, then resolve the thread.
- Never resolve a selected unresolved thread without first posting a direct thread reply with either the concrete fix summary or the code-level rationale for no change.
- For ambiguous threads that cannot be safely resolved, leave them unresolved and report exactly what is needed, unless the user's instruction explicitly says to clear them with a blocker reply.
- Re-fetch review threads after resolving and continue until the selected thread set is closed or a real blocker remains.

## 7) Report Results

Final response must include:

- PR URL or number.
- Pushed commit SHA, if any.
- Each reviewed thread and whether it was fixed by code or resolved with rationale only.
- Any unresolved blockers.
- Checks or verification actually run.

## Write Policy

This skill is intentionally write-capable. When it triggers, the default expectation is to commit, push, reply, and resolve when those actions are needed to complete the PR cleanup. Stop only when GitHub authentication, missing PR context, conflicting requirements, or unsafe ambiguity prevents correct action.
