# GitHub GraphQL

Diagnostic reference only. Use bundled scripts for normal fetch and resolution;
do not reconstruct these loops during sweep.

## Required feedback fields

PR metadata from `gh pr view --json`:

```text
number,url,title,state,baseRefName,headRefName,headRefOid,headRepository
```

Feedback connections:

```text
comments: id,url,body,createdAt,author.login
reviews: id,url,state,body,submittedAt,author.login
reviewThreads: id,isResolved,isOutdated,path,line,diffSide,startLine,
               startDiffSide,originalLine,originalStartLine
thread comments: id,url,body,createdAt,author.login
```

Resolution needs thread `id`; safety checks need `state`, `headRefOid`,
`headRefName`, and `headRepository.nameWithOwner`.

## Pagination contract

- Request `pageInfo { hasNextPage endCursor }` on every connection.
- Paginate PR comments, reviews, and review threads independently. Never stop
  because one connection finished.
- Do not restart completed connections and append duplicate first pages.
- Each thread's `comments` is another connection. Initial `first: 100` does not
  prove reply completeness. For every thread with `hasNextPage: true`, paginate
  replies by thread node ID until false.
- Treat GraphQL `errors`, missing PR/thread nodes, or absent cursors while
  `hasNextPage` as failure. Never return partial data as complete.

## Fetch query shape

```graphql
query Feedback(
  $owner: String!
  $repo: String!
  $number: Int!
  $commentsCursor: String
  $reviewsCursor: String
  $threadsCursor: String
) {
  repository(owner: $owner, name: $repo) {
    pullRequest(number: $number) {
      comments(first: 100, after: $commentsCursor) {
        pageInfo { hasNextPage endCursor }
        nodes { id url body createdAt author { login } }
      }
      reviews(first: 100, after: $reviewsCursor) {
        pageInfo { hasNextPage endCursor }
        nodes { id url state body submittedAt author { login } }
      }
      reviewThreads(first: 100, after: $threadsCursor) {
        pageInfo { hasNextPage endCursor }
        nodes {
          id isResolved isOutdated path line diffSide
          startLine startDiffSide originalLine originalStartLine
          comments(first: 100) {
            pageInfo { hasNextPage endCursor }
            nodes { id url body createdAt author { login } }
          }
        }
      }
    }
  }
}
```

Nested reply continuation:

```graphql
query ThreadReplies($threadId: ID!, $cursor: String) {
  node(id: $threadId) {
    ... on PullRequestReviewThread {
      comments(first: 100, after: $cursor) {
        pageInfo { hasNextPage endCursor }
        nodes { id url body createdAt author { login } }
      }
    }
  }
}
```

## Resolve and verify

Mutation:

```graphql
mutation Resolve($threadId: ID!) {
  resolveReviewThread(input: {threadId: $threadId}) {
    thread { id isResolved }
  }
}
```

Mutation response is not final verification. Re-fetch all paginated review thread
states and require every supplied ID exists with `isResolved: true`. Before write,
re-fetch PR metadata and require open PR plus local `HEAD == headRefOid`.
