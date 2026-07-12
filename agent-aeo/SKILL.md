---
name: agent-aeo
description: "Implement agent-oriented website access and AI crawler discovery for public websites. Use when adding or auditing /.well-known/agent.json, llms.txt, llms-full.txt, per-page index.md, per-page llms.txt, Accept: text/markdown negotiation, ?mode=agent markdown views, canonical markdown or plain-text page extraction, or other agent-friendly content routes and headers."
---

# Agent AEO

Expose public website content in machine-readable forms that agents can
discover, request, and cite without scraping rendered HTML. Use one content
resolver, thin route entry points, explicit content types, and runtime tests.

## Surfaces and references

Add only the surfaces that fit the site:

- discovery metadata: `/.well-known/agent.json`; read
  `references/agent-json.md` for its response contract
- root text entry points: `/llms.txt` and `/llms-full.txt`; read
  `references/llms-txt.md` for their response contracts
- page content: `/<path>/index.md`, `/<path>/llms.txt`, `?mode=agent`, and
  `Accept: text/markdown`; read `references/index-md.md` and
  `references/llms-txt.md` for their response contracts

Every page-level response must include real body content plus enough site
context for a deep link. Do not create a separate visual agent page when the
same markdown can be returned through `index.md`, `?mode=agent`, or
`Accept: text/markdown`.

## Recommended Architecture

Centralize content generation in one server-side module or handler; keep
framework routes, controllers, and middleware thin. Its content function accepts:

- `path`: requested canonical path
- `locale`: resolved locale when applicable
- `contentType`: `text/markdown` or `text/plain`

That function should:

- normalize `/index.md`, `/llms.txt`, and `?mode=agent` to the canonical path
- resolve page content from existing route registries, templates, Markdown
  sources, CMS exports, or static page data
- render markdown first
- down-convert to plain text only at the final response boundary when needed
- return `404` for unsupported paths instead of placeholder content

Use a shared proxy, dynamic route, rewrite, or router parameter instead of
identical per-page `index.md` or `llms.txt` files.

## Rewrite Pattern

If rewrites, middleware, or edge routing are available, route agent surfaces
through one central handler; otherwise use one dynamic catch-all handler.

The rewrite layer should:

- detect `/index.md` (including nested), nested `*/llms.txt` as plain text,
  `?mode=agent`, and supported URLs whose `Accept` includes `text/markdown`
- set `Vary: Accept` for content-negotiated responses
- resolve the canonical `path` before calling the content function: strip
  `/index.md`, `/llms.txt`, and `?mode=agent` (for example,
  `/services/index.md` becomes `/services`)
- pass the original requested path in a header and/or query parameter when the
  framework mutates URL state during rewrites
- leave root `/llms.txt`, `/llms-full.txt`, and `/.well-known/agent.json` to
  their root routes

## Discovery Metadata

Use `references/agent-json.md` for the response shape. Keep it static for
static sites; do not add auth, data fetching, or runtime dependencies only for
discovery.

## Tests

Add or update tests that verify behavior, not source formatting:

- `/.well-known/agent.json` returns JSON with advertised URLs or patterns
- root `/llms.txt` and `/llms-full.txt` return plain text
- `/path/index.md`, `/path?mode=agent`, and `Accept: text/markdown` return the
  same supported-page Markdown body; `/path/llms.txt` returns it as plain text
- nested deeper paths work, for example `/services/item/llms.txt`
- article `index.md` and `llms.txt` include the real article body
- root `/llms.txt` is not swallowed by the per-page `llms.txt` rewrite rule
- content-negotiated rewrites set `Vary: Accept`

Prefer request-level handler, route, or middleware tests over source grepping.

## Validation

Run route or handler tests, typecheck or production build, and lint or format
checks; smoke-test representative URLs when the rewrite layer changes.

Report warnings separately from pass or fail status. Treat missing article
bodies, placeholder content, and duplicated route files as defects.
