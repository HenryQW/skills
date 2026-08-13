# GitHub operations

Use bundled scripts instead of rebuilding GraphQL or remote-selection commands.
Resolve paths relative to this skill directory. For GraphQL field and pagination
contracts, see [GitHub GraphQL](github-graphql.md).

## Feedback snapshot

```bash
python scripts/fetch_feedback.py --output /tmp/pr-feedback.json
python scripts/fetch_feedback.py --pr https://github.com/OWNER/REPO/pull/123 --output /tmp/pr-feedback.json
python scripts/fetch_feedback.py --repo OWNER/REPO --pr 123 --output /tmp/pr-feedback.json
```

Fetcher authenticates with `gh`, requires clean worktree, open PR, and matching
local/remote head. Current-branch discovery also requires matching branch name.
It paginates conversation comments, reviews, review threads, and every thread's
nested replies. Snapshot preserves thread IDs and resolution state.

Inspect PR diff without writing:

```bash
gh pr diff "$(python -c 'import json,sys; print(json.load(open(sys.argv[1]))["pull_request"]["url"])' /tmp/pr-feedback.json)"
```

## Safe push

After scoped commit and clean-worktree validation:

```bash
python scripts/push_head.py --snapshot /tmp/pr-feedback.json
```

Script rejects changed remote PR head, finds exactly one configured GitHub remote
matching PR head repository across SSH/HTTPS URLs, pushes explicit
`HEAD:<headRefName>`, then verifies `headRefOid` equals local `HEAD`.

## Resolve addressed threads

Fetch fresh snapshot after push, then pass only addressed review thread IDs:

```bash
python scripts/resolve_threads.py --snapshot /tmp/pr-feedback-final.json THREAD_ID...
```

Resolver requires open PR, clean worktree, unchanged snapshot head, and local
`HEAD == headRefOid`. It resolves each supplied ID, re-fetches all paginated
thread states, and fails unless every supplied ID exists and reports
`isResolved: true`.

Underlying single-thread `gh` mutation, for diagnosis only:

```bash
gh api graphql \
  -f 'query=mutation($threadId:ID!){resolveReviewThread(input:{threadId:$threadId}){thread{id isResolved}}}' \
  -F threadId=THREAD_ID
```

## Checks

Read current check state only when needed. Never wait or poll:

```bash
gh pr checks PR
# forbidden: gh pr checks PR --watch --interval 10
```

Report pending checks; leave CI diagnosis or waiting to owning workflow.

## Keep agent-owned

Do not script feedback classification, code edits, repository-specific validation,
staging, or commit boundaries. Those need code and PR-intent judgment. Keep simple
read commands (`git status`, `git diff`, `gh pr diff`) here, not in wrappers.
