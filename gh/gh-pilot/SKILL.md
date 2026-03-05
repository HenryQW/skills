---
name: gh-pilot
description: Iteratively drive a PR through GitHub Copilot review using a simple loop with direct `gh` commands and no helper scripts. Reuse existing Copilot feedback first, fetch unresolved thread state via GraphQL, request/re-request Copilot when needed, and require a fresh Copilot pass after pushed fixes.
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

#### A. Fetch Copilot state first

```bash
gh api repos/<OWNER>/<REPO>/pulls/<PR_NUMBER>/reviews
```

Fetch review threads with resolution state (paginate if needed):

```bash
gh api graphql \
  -F owner="<OWNER>" \
  -F repo="<REPO>" \
  -F pr=<PR_NUMBER> \
  -f query='
query($owner: String!, $repo: String!, $pr: Int!, $cursor: String) {
  repository(owner: $owner, name: $repo) {
    pullRequest(number: $pr) {
      reviewThreads(first: 100, after: $cursor) {
        pageInfo { hasNextPage endCursor }
        nodes {
          id
          isResolved
          comments(first: 10) {
            nodes { id body author { login } createdAt }
          }
        }
      }
    }
  }
}'
```

From these results, compute:

- `last_copilot_review_id` from the latest review by:
  - `copilot-pull-request-reviewer[bot]`
  - `copilot-pull-request-reviewer`
  - `Copilot`
- `unresolved_copilot_thread_ids` from threads where:
  - `isResolved == false`
  - at least one comment author login is one of the Copilot logins above

#### B. Bootstrap decision

- If `unresolved_copilot_thread_ids` is not empty, skip reviewer request and process them.
- If there is no Copilot review yet, request Copilot review.
- If Step H pushed code in the previous iteration, request a fresh Copilot review.
- Stop successfully only when:
  - `unresolved_copilot_thread_ids` is empty, and
  - no new code was pushed since the latest Copilot review round.

#### C. Request Copilot review only when B says none exist

```bash
gh pr edit <PR_NUMBER> --add-reviewer "copilot-pull-request-reviewer"
```

If Copilot is already assigned and a fresh pass is needed:

```bash
gh pr edit <PR_NUMBER> --remove-reviewer "copilot-pull-request-reviewer"
gh pr edit <PR_NUMBER> --add-reviewer "copilot-pull-request-reviewer"
```

#### D. Wait for a new Copilot review (only when C ran)

Poll the reviews endpoint every 30 seconds until a **new** Copilot review appears
(review id differs from `last_copilot_review_id` captured in Step A).

Example:

```bash
LAST_ID="<LAST_COPILOT_REVIEW_ID_OR_0>"
for _ in {1..60}; do
  NEW_ID=$(gh api repos/<OWNER>/<REPO>/pulls/<PR_NUMBER>/reviews \
    --jq '[.[] | select(.user.login == "copilot-pull-request-reviewer[bot]" or .user.login == "copilot-pull-request-reviewer" or .user.login == "Copilot")] | last | .id // 0')
  if [ "$NEW_ID" != "0" ] && [ "$NEW_ID" != "$LAST_ID" ]; then
    break
  fi
  sleep 30
done
```

If no new Copilot review appears within 30 minutes, stop and report timeout.
After new review appears, re-run Step A.

Do not re-request Copilot again while waiting in this step.

#### E. Check exit conditions

Stop the loop if any condition is true:

- Latest Copilot review round is complete and `unresolved_copilot_thread_ids` is empty.
- Max iterations reached (report remaining items).

Never treat "resolved by the agent" alone as terminal after a push; require a
fresh Copilot review pass.

#### F. Process each Copilot thread

For each unresolved Copilot thread:

1. Read code context.
2. Classify as `Actionable` or `Non-actionable`.
3. If actionable, implement the fix and update tests/docs if needed.
4. If non-actionable, prepare a short rationale reply.

#### G. Resolve and reply on threads

Fetch unresolved threads (paginate if needed):

```bash
gh api graphql \
  -F owner="<OWNER>" \
  -F repo="<REPO>" \
  -F pr=<PR_NUMBER> \
  -f query='
query($owner: String!, $repo: String!, $pr: Int!, $cursor: String) {
  repository(owner: $owner, name: $repo) {
    pullRequest(number: $pr) {
      reviewThreads(first: 100, after: $cursor) {
        pageInfo { hasNextPage endCursor }
        nodes {
          id
          isResolved
          comments(first: 10) {
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
for THREAD_ID in <THREAD_ID_1> <THREAD_ID_2> <THREAD_ID_N>; do
  gh api graphql \
    -F threadId="$THREAD_ID" \
    -f query='
mutation($threadId: ID!) {
  resolveReviewThread(input: {threadId: $threadId}) {
    thread { isResolved }
  }
}'
done
```

If batching in one mutation, generate one alias per thread id (`t1..tN`) dynamically.

Reply to non-actionable comments with rationale:

```bash
gh api repos/<OWNER>/<REPO>/pulls/<PR_NUMBER>/comments -f body='Rationale here' -F in_reply_to=<COMMENT_ID>
```

#### H. Commit and push once for the iteration

```bash
git add -A
git commit -m "agent: address copilot review feedback (gh-pilot iteration N)"
git push
```

After pushing code changes, go to Step **C** to request a fresh Copilot pass.
If no code changes were made in this iteration, skip commit/push and return to Step **A**.

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
