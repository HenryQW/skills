# `llms.txt` format

Use this reference when implementing root `llms.txt`, root `llms-full.txt`, or
page-level plain-text `llms.txt` views.

## Response contract

- Return `text/plain; charset=utf-8`.
- Return plain text, not HTML and not JSON.
- Preserve headings, paragraphs, and lists as readable text.
- Do not emit Markdown-only features that depend on HTML rendering.
- Keep URLs absolute when they are intended as discovery links.

## Root `llms.txt`

Use root `llms.txt` as the compact machine-readable entry point for the site.

Include:

- site or organization name
- one short description of what the site is
- canonical origin
- default locale and supported locales when relevant
- links to major sections or high-value pages
- link to `llms-full.txt` when present
- note about markdown access patterns when the site supports them

Recommended shape:

```text
Example Website

Example Website is a leading provider of widgets and widget-related services.

Canonical URL: https://example.com
Default locale: en-US
Locales: en-US, zh-Hans, zh-Hant

Primary resources:
- Home: https://example.com/en-US
- Services: https://example.com/en-US/services
- Insights: https://example.com/en-US/insights
- Full corpus: https://example.com/llms-full.txt

Markdown access:
- Add /index.md to a page URL
- Add ?mode=agent to a page URL
- Send Accept: text/markdown to supported page URLs
```

## Root `llms-full.txt`

Use root `llms-full.txt` for the fuller machine-readable map or corpus.

It may include:

- larger section inventories
- key page summaries
- article inventories
- route catalogs
- content excerpts when the site intentionally exposes them

Do not make `llms-full.txt` contradict `llms.txt`. The shorter file should be a
compact entry point; the fuller file should expand on it.

## Page-level `llms.txt`

Use page-level `llms.txt` as the plain-text representation of one page.

Include:

- page title
- short site context
- canonical URL
- locale when relevant
- body content rendered as readable plain text

Recommended shape:

```text
Page Title

Site: Example Website
Context: Example Website is a leading provider of widgets and widget-related services.
Canonical URL: https://example.com/en-US/services/widget-management

[Plain-text body content here]
```

For article pages, include the actual article body, not only summary metadata.

## Normalization rules

- Convert Markdown to plain text at the response boundary when possible.
- Strip frontmatter and route-only metadata before rendering.
- Preserve heading order and paragraph order.
- Preserve list semantics in readable text form.
- Avoid duplicate repeated boilerplate on every page unless it is needed for
  standalone context.
