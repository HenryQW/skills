# Details

## Description

Search for issues on GitHub.

The command supports constructing queries using the GitHub search syntax,
using the parameter and qualifier flags, or a combination of the two.

GitHub search syntax is documented at:
<https://docs.github.com/search-github/searching-on-github/searching-issues-and-pull-requests>

On supported GitHub hosts, advanced issue search syntax can be used in the
`--search` query. For more information about advanced issue search, see:
<https://docs.github.com/en/issues/tracking-your-work-with-issues/using-issues/filtering-and-searching-issues-and-pull-requests#building-advanced-filters-for-issues>

Use `--search-type` to select semantic or hybrid (keyword + semantic)
ranking instead of the default lexical search. Semantic and hybrid search are
scoped to issues, are relevance-ranked (so `--sort` and `--order`
cannot be used), return a single page of results, and are not available on
GitHub Enterprise Server.

For more information on handling search queries containing a hyphen, run `gh search --help`.

For more information about output formatting flags, see `gh help formatting`.

## Json Fields

  assignees, author, authorAssociation, body, closedAt, commentsCount, createdAt,
  id, isLocked, isPullRequest, labels, number, repository, state, title,
  updatedAt, url
