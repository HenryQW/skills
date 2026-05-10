# `/.well-known/agent.json` format

Use this reference when implementing discovery metadata for agent clients.

## Response contract

- Return `application/json; charset=utf-8`.
- Keep the file stable and machine-readable.
- Prefer a static response when the site is static.
- Avoid secrets, auth requirements, or user-specific data.

## Required information

Expose the core information an agent needs to discover the site’s alternate
machine-readable surfaces:

- site name
- canonical origin
- default locale when relevant
- supported locales when relevant
- root `llms.txt` URL
- root `llms-full.txt` URL when present
- page-level markdown access pattern
- page-level plain-text access pattern

Recommended shape:

```json
{
  "siteName": "Example Website",
  "origin": "https://example.com",
  "defaultLocale": "en-US",
  "locales": ["en-US", "zh-Hans", "zh-Hant"],
  "discovery": {
    "llmsTxt": "https://example.com/llms.txt",
    "llmsFullTxt": "https://example.com/llms-full.txt"
  },
  "pageFormats": {
    "markdown": [
      "https://example.com/{path}/index.md",
      "https://example.com/{path}?mode=agent",
      "Accept: text/markdown on supported page URLs"
    ],
    "plainText": [
      "https://example.com/{path}/llms.txt"
    ]
  }
}
```

## Field guidance

- Keep URLs absolute.
- Keep pattern strings explicit enough that an agent can construct requests.
- Include locale-specific patterns when the site is locale-prefixed.
- Omit fields that the site does not actually support.
- Keep naming internally consistent across the file. The exact JSON keys may
  vary by implementation, but the semantics should remain clear.

## Scope rules

- Do not use this file as a dump of all routes.
- Do not duplicate full page content here.
- Do not advertise formats or negotiation modes that the site does not
  implement.

This file should tell agents where to go next, not replace `llms.txt` or
`index.md`.
