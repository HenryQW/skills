---
name: gh-pilot
description: Iteratively drive a PR through GitHub Copilot review using a simple loop. Check for existing Copilot feedback first, request review only when needed, then fix actionable comments, resolve or reply on threads, push once, and repeat until no unresolved Copilot comments remain.
---

# GH Pilot

Run a lightweight Copilot review loop on one PR until feedback is fully addressed.

## Inputs

- **PR number** (optional): If not provided, detect the PR for the current branch.

## Instructions

### 1. Identify the PR

```bash
gh pr view --json number,headRefName -q '{number: .number, branch: .headRefName}'
```

### 2. Loop

Repeat this cycle. **Max 5 iterations** to avoid runaway loops.

#### A. Fetch Copilot results first

```bash
gh api repos/{owner}/{repo}/pulls/<PR_NUMBER>/reviews
gh api repos/{owner}/{repo}/pulls/<PR_NUMBER>/comments
```

Use only the latest review and comments from:

- `copilot-pull-request-reviewer[bot]`
- `copilot-pull-request-reviewer`

#### B. Bootstrap decision

- If there are unresolved Copilot comments, skip reviewer request and process them.
- If there are no Copilot reviews and no Copilot comments, request Copilot review.
- If Copilot already reported no unresolved comments, stop successfully.

#### C. Request Copilot review only when B says none exist

```bash
gh pr edit <PR_NUMBER> --add-reviewer "copilot-pull-request-reviewer"
```

If Copilot is already assigned and a fresh pass is needed:

```bash
gh pr edit <PR_NUMBER> --remove-reviewer "copilot-pull-request-reviewer"
gh pr edit <PR_NUMBER> --add-reviewer "copilot-pull-request-reviewer"
```

#### D. Wait for checks and refresh Copilot results (only when C ran)

```bash
gh pr checks <PR_NUMBER> --watch
```

If checks are still pending after watch exits, poll every 30 seconds until terminal states, then re-run Step A.

#### E. Check exit conditions

Stop the loop if any condition is true:

- Latest Copilot review says it generated no comments.
- There are zero unresolved Copilot review comments.
- Max iterations reached (report remaining items).

#### F. Process each Copilot thread

For each unresolved Copilot thread:

1. Read code context.
2. Classify as `Actionable` or `Non-actionable`.
3. If actionable, implement the fix and update tests/docs if needed.
4. If non-actionable, prepare a short rationale reply.

#### G. Resolve and reply on threads

Fetch unresolved threads (paginate if needed):

```bash
gh api graphql -f query='
query($cursor: String) {
  repository(owner: "OWNER", name: "REPO") {
    pullRequest(number: PR_NUMBER) {
      reviewThreads(first: 100, after: $cursor) {
        pageInfo { hasNextPage endCursor }
        nodes {
          id
          isResolved
          comments(first: 1) {
            nodes { id body author { login } }
          }
        }
      }
    }
  }
}'
```

Resolve addressed threads:

```bash
gh api graphql -f query='
mutation {
  t1: resolveReviewThread(input: {threadId: "ID1"}) { thread { isResolved } }
  t2: resolveReviewThread(input: {threadId: "ID2"}) { thread { isResolved } }
}'
```

Reply to non-actionable comments with rationale:

```bash
gh api repos/{owner}/{repo}/pulls/<PR_NUMBER>/comments -f body='Rationale here' -F in_reply_to=<COMMENT_ID>
```

#### H. Commit and push once for the iteration

```bash
git add -A
git commit -m "agent: address copilot review feedback (gh-pilot iteration N)"
git push
```

Then repeat from step **A**.

### 3. Report

At the end, summarize:

| Field                      | Value                         |
| -------------------------- | ----------------------------- |
| Iterations                 | N                             |
| Copilot comments resolved  | N                             |
| Copilot comments remaining | N                             |
| Final state                | Success or max-iteration stop |

## Output format

```
gh-pilot complete.
  Iterations:    N
  Resolved:      X comments
  Remaining:     Y
  Final state:   success|max-iteration-stop
```
