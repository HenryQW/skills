---
name: agent-aeo
description: "Implement agent-oriented website access and AI crawler discovery for public websites. Use when adding or auditing /.well-known/agent.json, llms.txt, llms-full.txt, per-page index.md, per-page llms.txt, Accept: text/markdown negotiation, ?mode=agent markdown views, canonical markdown or plain-text page extraction, or other agent-friendly content routes and headers."
---

# Agent AEO

Use this skill to expose a public website in machine-readable forms that agents
can discover, request, and cite without scraping rendered HTML.

Keep the implementation boring: one content resolver, thin route or proxy entry
points, explicit content types, and tests that exercise runtime behavior.

Read these references when you need format-level detail:

- `references/llms-txt.md`: structure and response rules for `llms.txt` and
  `llms-full.txt`
- `references/index-md.md`: structure and response rules for page-level
  markdown views
- `references/agent-json.md`: structure and response rules for
  `/.well-known/agent.json`

## Target Surfaces

Implement these surfaces when they fit the site:

- `/.well-known/agent.json`: discovery metadata for agent clients.
- `/llms.txt`: compact root plain-text entry point with site summary and links.
- `/llms-full.txt`: fuller root plain-text corpus or route catalog.
- `/<path>/index.md`: markdown representation of the page content.
- `/<path>/llms.txt`: plain-text representation of the same page content.
- `?mode=agent`: alternate markdown view for the canonical page URL.
- `Accept: text/markdown`: content negotiation for supported page URLs.

Do not create a separate visual agent page when the site can return the same
markdown through `index.md`, `?mode=agent`, and `Accept: text/markdown`.

## Content Contract

Every page-level agent response must include enough standalone context for a
direct deep link:

- page title as the first heading
- concise site or organization context near the top
- canonical URL
- locale, if the site is localized
- the actual page body content, not only metadata
- source links and dates when they are meaningful

For subpages, prepend a consistent site context block before page-specific
content. Example shape:

```md
# Page Title

Site: Example Website
Context: Example Website is a leading provider of widgets and widget-related services.
Canonical URL: https://example.com/en-US/services/widget-management
```

For article or publication pages, include the actual body from the source
Markdown, MDX, CMS export, or other canonical source after frontmatter or
metadata removal. Do not stop at summary, tags, or excerpt.

For exact formatting expectations, read the matching reference file instead of
inventing a new shape.

## Recommended Architecture

Centralize content generation in a single server-side module or handler layer.
Framework-specific route files, controllers, handlers, or middleware should stay
thin.

Expose one content function that accepts:

- `path`: requested canonical path
- `locale`: resolved locale when applicable
- `contentType`: `text/markdown` or `text/plain`

That function should:

- normalize `/index.md`, `/llms.txt`, and `?mode=agent` to the canonical page
  path
- resolve page content from existing route registries, templates, Markdown
  sources, CMS exports, or static page data
- render markdown first
- down-convert to plain text only at the final response boundary when needed
- return `404` for unsupported paths instead of placeholder content

Keep per-page route duplication out of the codebase. Avoid one identical
`index.md` or `llms.txt` route file per page folder when a shared proxy,
dynamic route, rewrite layer, or router parameter can handle all requests.

## Rewrite Pattern

If the framework supports rewrites, middleware, or edge routing, route agent
surfaces through one central handler.

Use a small resolver object instead of repeating inline branches:

```ts
type AgentRewrite = {
  contentType: "text/markdown" | "text/plain";
  locale?: string;
  requestedPath: string;
  varyAccept: boolean;
};
```

The rewrite layer should:

- detect `/index.md` and nested `*/index.md`
- detect nested `*/llms.txt` and mark them plain text
- detect `?mode=agent`
- detect supported page URLs when `Accept` includes `text/markdown`
- set `Vary: Accept` for content-negotiated responses
- pass the original requested path in a header and or query parameter when the
  framework mutates URL state during rewrites
- leave root `/llms.txt`, `/llms-full.txt`, and `/.well-known/agent.json`
  owned by their root routes

When the framework does not support rewrites cleanly, use one dynamic catch-all
route or equivalent request handler instead.

## Discovery Metadata

Use `references/agent-json.md` for the response shape. Keep this file static
when the site is static. Do not add auth, data fetching, or runtime
dependencies only for discovery.

## Tests

Add or update tests that verify behavior, not source formatting:

- `/.well-known/agent.json` returns JSON with the advertised URLs or patterns
- root `/llms.txt` and `/llms-full.txt` return plain text
- `/path/index.md`, `/path?mode=agent`, and `Accept: text/markdown` return the
  same markdown body for supported pages
- `/path/llms.txt` returns the same page content as plain text
- nested deeper paths work, for example `/services/item/llms.txt`
- article `index.md` and `llms.txt` include the real article body
- root `/llms.txt` is not swallowed by the per-page `llms.txt` rewrite rule
- content-negotiated rewrites set `Vary: Accept`

Prefer request-level tests against handlers, routes, or middleware over source
grepping.

## Validation

Run the site's normal gates for route, rendering, or content changes:

- route or handler tests for agent surfaces and rewrites
- typecheck or production build
- lint or format checks
- a runtime smoke test against representative URLs when the rewrite layer
  changed

Report warnings separately from pass or fail status. Treat missing article
bodies, placeholder content, and duplicated route files as defects.
