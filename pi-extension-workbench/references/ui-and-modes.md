# UI and Modes

Navigation aid distilled from published examples. Verify exact methods in
installed `docs/extensions.md` section `Custom UI`; use `docs/tui.md` only for
custom components.

## Mode gate

| Mode | `ctx.mode` | `ctx.hasUI` | Safe UI |
|---|---|---:|---|
| Interactive | `tui` | true | Full TUI |
| RPC | `rpc` | true | Protocol-backed dialogs, notifications, status, widgets; `custom()` returns `undefined` |
| JSON | `json` | false | No prompts; UI calls are no-ops |
| Print | `print` | false | No prompts |

- Check `ctx.hasUI` for dialogs and UI methods supported by TUI and RPC.
- Check `ctx.mode === "tui"` for `custom()`, component factories, overlays,
  custom editors, and terminal input.
- Dangerous action needing confirmation must define non-UI behavior explicitly;
  safest default is block.

## Pick smallest UI

1. `notify`, `confirm`, `select`, `input`, or `editor`.
2. `setStatus`, `setWidget`, `setTitle`, or editor text for persistent chrome.
3. Message/tool/entry renderer for transcript formatting.
4. `custom()` only when standard controls cannot express interaction.

Dialogs support `timeout`. Use `AbortSignal` only when code must distinguish
manual cancel from timeout. See `timed-confirm.ts`.

`sendMessage` + `registerMessageRenderer` affects model context.
`appendEntry` + `registerEntryRenderer` is durable TUI-only data. Do not choose
based on appearance alone. See `message-renderer.ts` and `entry-renderer.ts`.

## Custom component rules

- Return width-bounded lines; use `truncateToWidth` and theme tokens.
- Handle configured keybindings with Pi TUI helpers, close on expected cancel
  keys, and call `tui.requestRender()` after state changes.
- Cache rendering only when invalidation clears cache.
- Extend `CustomEditor`, not base `Editor`; call `super.handleInput()` for keys
  not owned. Wrap prior editor factory instead of replacing other extension
  behavior blindly.
- Clear timers and UI state on completion or `session_shutdown`.
- Keep renderers synchronous and free of I/O.

## Published examples

| Need | Path |
|---|---|
| RPC-supported UI surface | `rpc-demo.ts` |
| Status and widget placement | `status-line.ts`, `widget-placement.ts` |
| Settings selector | `tools.ts` |
| Custom editor | `modal-editor.ts` |
| Transcript rendering | `message-renderer.ts`, `entry-renderer.ts` |
| Tool rendering | `todo.ts`, `truncated-tool.ts` |
| Overlay behavior | `overlay-test.ts`, `overlay-qa-tests.ts` |
| Autocomplete composition | `github-issue-autocomplete.ts` |

Paths are relative to `$PI_CODING_AGENT_ROOT/examples/extensions/`.
