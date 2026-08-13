---
name: pi-extension-workbench
description: Use when developing, modifying, or debugging a Pi extension or Pi extension package, including requests identified only by package name.
---

# Pi Extension Workbench

Use APIs and patterns shipped with active published Pi version, not memory or a
source checkout.

## Resolve authority

Run reusable resolver. It prints root of package loaded by active `pi` command,
including package-manager launcher shims, and fails on invalid assumptions:

```bash
PI_CODING_AGENT_ROOT="$(<skill_dir>/scripts/resolve-authority.sh)"
export PI_CODING_AGENT_ROOT
```

Record printed path. Shell tool calls do not share exports; start every later
one-shot shell call with `PI_CODING_AGENT_ROOT='<printed-path>'` and export it
when child processes need it.

Installed package docs, examples, and types define active runtime. Do not
replace them with GitHub, local Pi source clones, or remembered APIs.

## Load progressively

Read target manifest and entry points, then load only matching reference:

- Events, cleanup, compaction, branch-aware state:
  [lifecycle-and-state.md](references/lifecycle-and-state.md)
- Tools, commands, flags, messages, dynamic activation:
  [tools-and-commands.md](references/tools-and-commands.md)
- Dialogs, TUI components, rendering, RPC/JSON/print behavior:
  [ui-and-modes.md](references/ui-and-modes.md)
- Package manifests, dependencies, resources, providers, package-named work:
  [packages-and-integrations.md](references/packages-and-integrations.md)

Then search installed references for exact API and read only matching docs
section plus closest example:

```bash
PI_CODING_AGENT_ROOT='<printed-path>'
rg -nF '<API-or-behavior>' "$PI_CODING_AGENT_ROOT/docs/extensions.md" \
  "$PI_CODING_AGENT_ROOT/docs/packages.md" \
  "$PI_CODING_AGENT_ROOT/examples/extensions"
```

Read published type declarations only when docs and example do not settle
signature. Do not read full extension guide by default.

## Work

1. Read repository instructions, manifest, entry point, callers, tests, and
   neighboring patterns. Treat package-named request as extension work only
   when manifest, conventional extension directory, or default extension factory
   using `ExtensionAPI` identifies an extension entry point.
2. Inspect target Pi dependency/peer range and active installed version before
   selecting API. Active package defines current runtime; target's declared
   support floor remains compatibility constraint.
3. Match request to smallest official example. Reuse `ExtensionAPI`, context,
   events, UI, session, settings, and Node APIs. Copy pattern, not scaffolding.
4. For bugs, trace all callers and fix shared root cause. Preserve trust-boundary
   validation, visible errors, resource cleanup, and branch/session semantics.
5. Make smallest focused change. Add no speculative compatibility path,
   abstraction, config, or dependency.
6. Add or update one high-value test for non-trivial logic using target's test
   style. Run focused test and package typecheck/build. Smoke-load with active
   published `pi` when load or lifecycle changed and doing so is safe.
7. Update target README for changed commands, config, tools, or behavior. Do not
   bump version, pack for release, install, or publish unless requested.

When installed reference lacks capability, or target support floor cannot be
verified for chosen API, stop and report incompatibility instead of inventing a
fallback. Report exact validation and untested interactive behavior.
