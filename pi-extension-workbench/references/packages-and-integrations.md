# Packages and Integrations

Navigation aid distilled from published `docs/packages.md` and extension
examples. Verify manifest and provider contracts in installed docs before edits.

## Recognize package-shaped work

A request naming repository or package such as `pi-auto-dag` still counts as Pi
extension work when `package.json` has `pi.extensions`, conventional
`extensions/`, or imports `@earendil-works/pi-coding-agent`. Inspect manifest,
entry points, lockfile, and package scripts before choosing API.

Check target Pi dependency or peer range against active package version:

```bash
node -p 'require(process.env.PI_CODING_AGENT_ROOT + "/package.json").version'
node -e 'const p=require("./package.json"); console.log({dependencies:p.dependencies,peerDependencies:p.peerDependencies,devDependencies:p.devDependencies,engines:p.engines})'
```

Installed package defines active runtime. Broad target support range adds a
compatibility constraint: do not use API shown only in current installed docs
until target types, tests, changelog, or version-matched published material prove
supported floor has it. Fail with clear incompatibility instead of adding a
silent fallback.

## Package manifest

Prefer explicit manifest when publishing mixed resources:

```json
{
  "type": "module",
  "keywords": ["pi-package"],
  "pi": {
    "extensions": ["./extensions"],
    "skills": ["./skills"],
    "prompts": ["./prompts"],
    "themes": ["./themes"]
  }
}
```

Without `pi` manifest, Pi discovers conventional `extensions/`, `skills/`,
`prompts/`, and `themes/` directories.

- Runtime third-party libraries belong in `dependencies`.
- Pi core imports belong in `peerDependencies` with `"*"` and must not be
  bundled: `@earendil-works/pi-ai`, `@earendil-works/pi-agent-core`,
  `@earendil-works/pi-coding-agent`, `@earendil-works/pi-tui`, `typebox`.
- A Pi package dependency whose resources must load from this package belongs
  in both `dependencies` and `bundledDependencies`; list its resource paths
  under `node_modules/` in `pi` manifest.
- Use `npm pack --dry-run` to inspect publish contents. Never version or publish
  unless requested.

See `$PI_CODING_AGENT_ROOT/docs/packages.md` and
`examples/extensions/with-deps/package.json`.

## Resources and extension boundaries

- Static package resources belong in manifest. Use `resources_discover` only
  for runtime-computed paths. Resolve sibling paths with `import.meta.url`, not
  process cwd. See `dynamic-resources/index.ts`.
- Use namespaced `pi.events` for in-process extension communication. No replay
  or persistence; restore needed state separately. See `event-bus.ts`.
- Provider payload hooks inspect or replace request/response transport data.
  Never log credentials or authorization headers. See `provider-payload.ts`.
- `registerProvider` is for proxies, custom auth, model catalogs, or streaming
  implementations—not ordinary model selection. Pass cancellation signals to
  network I/O. Start with `custom-provider-gitlab-duo/`; use
  `custom-provider-anthropic/` only when custom streaming/OAuth is required.
- Packages execute arbitrary code. Preserve trust checks for project-local code
  and validate all external config, paths, events, and provider data.

Paths are relative to `$PI_CODING_AGENT_ROOT/examples/extensions/` unless noted.
