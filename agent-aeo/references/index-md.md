# `index.md` format

Use this reference when implementing page-level markdown views exposed through
`/index.md`, `?mode=agent`, or `Accept: text/markdown`.

## Response contract

- Return `text/markdown; charset=utf-8`.
- Return the same logical content across `/index.md`, `?mode=agent`, and
  `Accept: text/markdown` for the same page.
- Use Markdown, not HTML fragments.
- Keep the response standalone so a deep-linked page still has enough site
  context.

## Required content

Include these elements near the top:

- H1 page title
- site or organization context
- canonical URL
- locale when relevant
- source links and dates when they are meaningful

Then include the actual page body content.

## Subpage context

For subpages, include a consistent site context block before page-specific
content so that agents accessing the page directly still understand the parent
site and organization.

That shared block should be stable across the site, except for canonical URL and
locale values.

## Articles and long-form content

For articles, insights, research, or publications:

- strip frontmatter
- keep real headings and paragraphs
- keep pull quotes, lists, and section structure in Markdown form
- include publication date when it is part of the page contract
- include source links when they help agents cite or verify the page
- include tags only if they are additive, not a substitute for body content

Do not stop at excerpt, hero summary, or metadata.

## Normalization rules

- Normalize `/index.md`, `?mode=agent`, and negotiated markdown requests to the
  same canonical page content.
- Reuse one shared content resolver when possible.
- Avoid separate handwritten `index.md` route files per page if the framework
  can centralize them.
- Return `404` for unsupported paths instead of placeholder Markdown.

## Consistency checks

The following should match for a supported page:

- page title
- canonical URL
- main body sections
- article body

Minor formatting differences between Markdown and plain text are acceptable, but
the underlying content should be the same.
