---
name: agent-aeo
description: "Implement agent-oriented website access and AI crawler discovery for public websites. Use when adding or auditing /.well-known/agent.json, llms.txt, llms-full.txt, per-page index.md, per-page llms.txt, Accept: text/markdown negotiation, ?mode=agent markdown views, canonical markdown or plain-text page extraction, or other agent-friendly content routes and headers."
---

# Agent AEO

Expose public site content without scraping rendered HTML. Add only the
surfaces the site needs:

- `/.well-known/agent.json`: `application/json; charset=utf-8`; advertise only
  implemented absolute URLs or patterns, locales, and canonical origin. Keep it
  static when possible and never include secrets or user-specific data.
- `/llms.txt` and optional `/llms-full.txt`: `text/plain; charset=utf-8` compact
  and expanded site maps with absolute discovery links.
- `/<path>/index.md`, `?mode=agent`, and `Accept: text/markdown`:
  `text/markdown; charset=utf-8` representations of the same canonical page.
- `/<path>/llms.txt`: the same page rendered as readable plain text.

Use one server-side resolver accepting canonical `path`, optional `locale`, and
output content type. Resolve existing route, Markdown, CMS, template, or static
data; render Markdown first and convert to plain text only at the response
boundary. Return `404` for unsupported paths. Page responses must include the
real body, title, canonical URL, and enough site context for a deep link;
articles must not stop at excerpts or metadata.

Route these surfaces through one dynamic handler, rewrite, proxy, or middleware
path rather than per-page files. Normalize agent suffixes and `?mode=agent`
before resolution, preserve the original path when a framework rewrite loses
it, set `Vary: Accept` for negotiated responses, and keep root discovery routes
out of page-level catch-alls. Do not create a separate visual agent page.

## Tests

Use request-level tests for behavior, not source formatting:

- advertised root routes return their declared content types;
- Markdown variants share canonical content and plain text preserves it;
- nested paths and article bodies work;
- page catch-alls do not swallow root routes;
- negotiated responses set `Vary: Accept`.

Run the focused route tests plus the repository's typecheck/build and lint; smoke
test representative URLs when routing changes. Missing bodies, placeholder
content, or duplicated route files are defects, not warnings.
