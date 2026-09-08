---
name: pencil-to-figma-migration
description: Migrate a project's Pencil design source and workflow to Figma through Figwright, including design reconstruction, component and token reuse, visual verification, repository cutover, and cleanup of .pen files, Pencil configuration, exports, and references. Use when asked to replace Pencil with Figma, migrate design.pen or another .pen file to Figma, adopt Figwright, or remove Pencil artifacts after a verified migration.
---

# Pencil to Figma Migration

Migrate the editable design source and the repository workflow to **Figma via Figwright**. Treat this as a verified reconstruction and cutover, not a filename conversion.

## Non-negotiable facts

- Figwright writes to and reads from a connected Figma file; it does not directly import `.pen` files.
- Keep the Pencil source until the scoped Figma result is complete and visually verified.
- Reuse the destination Figma file's variables, styles, components, and conventions before creating anything.
- Do not change product UI code unless the user also asks for implementation.
- Preserve unrelated repository changes and never delete an asset merely because it lived beside the `.pen` file.

## 1. Establish scope and source of truth

Read the repository instructions and inspect the working tree. Determine:

- which `.pen` file, pages, components, and responsive variants are in scope;
- which Figma file and page are the destination;
- whether the request is design migration only, repository cutover only, or both;
- which files are source-only, generated, runtime-owned, or shared with production.

If the destination or scope is ambiguous, ask one focused question. Otherwise proceed.

Record a small mapping while working:

```text
Pencil page/component (name + source id) -> Figma page/component (name + node id) -> verified
```

## 2. Inventory before mutation

Find the legacy source, sidecars, exports, configuration, docs, and references. Include hidden and ignored files because old renders commonly live in `.context/`:

```bash
rg --hidden --no-ignore -n -i '\bpencil\b|design\.pen|\.pen\b|Pen\.app|mcp-server-darwin' \
  --glob '!node_modules/**' --glob '!.git/**' --glob '!.next/**' \
  --glob '!coverage/**' --glob '!dist/**' .

rg --files --hidden --no-ignore \
  -g '!node_modules/**' -g '!.git/**' -g '!.next/**' \
  -g '!coverage/**' -g '!dist/**' \
  | rg -i '(^|/)(pencil|pen)(/|\.|$)|design\.pen$'
```

Classify every result before editing:

- **Design source:** `.pen`, source-only vectors, image placeholders.
- **Generated:** sidecars such as `DESIGN.json`, HTML renders, screenshots, DOM extraction scripts.
- **Workflow:** MCP config, agent instructions, README/design docs.
- **Implementation:** comments, tests, specs, and code that cite the old source.
- **Unrelated language:** common-noun uses such as “pencil sketch”; do not rewrite these unless zero literal matches are explicitly required.

Do not delete anything yet.

## 3. Connect and ground Figma

Require the Figwright plugin to be open in the target Figma file. Run `ping`; stop with a clear instruction if it is not connected.

Inspect the destination before writing:

1. `get_metadata` and `get_pages` — confirm the file and target page.
2. `get_variable_defs` — inventory reusable variables and modes.
3. `get_styles` — inventory shared paint, text, effect, and grid styles.
4. `get_local_components` or `scan_components` — inventory components and variants.
5. `get_design_context` and `get_screenshot` — understand nearby naming, structure, and visual conventions.

Never infer measurements or colors from screenshots when structured source or destination data exists. Screenshots are for visual verification.

## 4. Reconstruct in dependency order

Migrate only what is missing, in this order:

```text
variables -> shared styles -> base components -> variants -> page frames
```

For each item:

- reuse an existing Figma variable, style, or component when its role matches;
- bind variables and styles instead of hardcoding values;
- use component instances instead of copied subtrees;
- preserve semantic names and stable mobile/tablet/desktop relationships;
- use auto layout for related content and constraints for responsive behavior;
- import original vectors or images only when they are genuine source assets;
- batch independent or atomic Figwright writes when practical;
- keep a source-to-destination node mapping.

Do not recreate an entire design system merely because the source uses different names. Map equivalent roles first; create a new destination primitive only when no equivalent exists.

## 5. Verify before cutover

For every scoped page and component:

1. Compare the Figma screenshot with a trusted Pencil render or approved reference.
2. Check mobile, tablet, and desktop variants when they exist.
3. Inspect node structure, text, auto layout, constraints, and clipping.
4. Confirm colors, dimensions, and typography are variable/style-bound where equivalents exist.
5. Confirm component instances remain attached and variant properties survive resizing.

A migration is not complete when it only “looks close.” It must preserve content, hierarchy, responsive intent, and reusable design-system relationships.

Do not delete the legacy source until this verification passes or the user explicitly accepts named gaps.

## 6. Cut over the repository

Once Figma is verified, make ownership explicit: Figma is the editable design source and Figwright is the bridge. Update project instructions, design-system docs, README files, specs, comments, and test names to say **Figma via Figwright** where they describe the active workflow.

Remove only verified legacy artifacts:

- `.pen` design sources;
- generated sidecars that existed only for the old design source;
- source-only assets with no remaining runtime or documentation references;
- Pencil MCP configuration;
- temporary renders, exports, DOM scripts, screenshots, and caches;
- stale file-tree entries and old node ids in docs.

Do not blindly replace historical prose if doing so would make it false. Rewrite it to describe the current Figma source or remove obsolete detail.

## 7. Scan again

Repeat both deep scans from step 2 after cleanup. A successful cutover has:

- no legacy design-tool references in active project files;
- no `.pen` files or Pencil-specific filenames;
- explicit Figma/Figwright workflow guidance;
- no deleted asset still referenced by production or docs;
- no unrelated working-tree changes mixed into the migration.

Run `git diff --check` and parse any edited JSON configuration. Use the project's full test/build gates only when runtime, generated, or renderable application behavior changed; otherwise report the docs/config-only validation performed.

## Completion report

Report concisely:

- what was reconstructed in Figma and how it was verified;
- which legacy files and workflow references were removed;
- which scans or repository checks passed;
- any deliberately retained artifact and why.
