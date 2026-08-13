# Tools and Commands

Navigation aid distilled from published examples. Verify exact signatures in
installed `docs/extensions.md` sections headed `ExtensionAPI Methods` and
`Custom Tools` before editing code.

## Tool contract

- Register narrow TypeBox schema. Use `StringEnum` from
  `@earendil-works/pi-ai` for string enums; `Type.Union` of literals is not
  Google-compatible.
- Put LLM-facing result in `content` and renderer/state data in `details`.
  Throw from `execute()` to produce failed tool result; returned error-looking
  content is still success.
- Honor `signal`; use `onUpdate` only for useful progress. Prefer
  `pi.exec(command, args, { signal })` over shell string assembly.
- Bound output with Pi truncation helpers and preserve full output when users or
  model may need it. See `truncated-tool.ts`.
- Name tool in every `promptGuidelines` bullet. Guidelines are appended flat,
  without automatic tool-name prefix.
- Add `renderCall` or `renderResult` only when default rendering loses needed
  information. Renderers must handle partial, absent, error, collapsed, and
  expanded results.
- A tool sharing built-in name overrides behavior. Preserve built-in contract
  and fail closed at trust boundaries. See `tool-override.ts` and
  `built-in-tool-renderer.ts`.
- Shared mutable tool state may need `executionMode: "sequential"`; use only
  when parallel calls would race. See `tic-tac-toe.ts`.
- `terminate: true` skips follow-up only when every finalized result in batch
  terminates. See `structured-output.ts`.

## Dynamic tools

Register tools at factory load unless runtime discovery is needed. Runtime
registration works from `session_start` and commands. To progressively expose
registered tools:

1. Register all candidates.
2. Keep loader active and candidates inactive.
3. During loader execution, add matches with `pi.setActiveTools()` without
   removing current tools.
4. Let Pi record newly active definitions for next model request.

Use `pi.getAllTools()` metadata and `sourceInfo`; do not infer provenance from
names or paths. See `dynamic-tools.ts`, `kimi-deferred-tools.ts`, and `tools.ts`.

## Commands and messages

| Need | API | Rule | Published example |
|---|---|---|---|
| User-only action | `registerCommand` | Validate args; command context owns session replacement/reload APIs | `reload-runtime.ts` |
| CLI configuration | `registerFlag` / `getFlag` | Register in factory; parse once at session boundary | `preset.ts` |
| Keyboard action | `registerShortcut` | Avoid collision with built-ins | `plan-mode/index.ts` |
| Actual user turn | `sendUserMessage` | While streaming, set `deliverAs: "steer"` or `"followUp"` | `send-user-message.ts` |
| LLM-context custom message | `sendMessage` | Choose delivery and `triggerTurn` deliberately | `message-renderer.ts` |
| Durable non-LLM data | `appendEntry` | Pair with entry renderer only for TUI display | `entry-renderer.ts` |
| Cross-extension signal | `pi.events` | Namespace event names; treat payload as untrusted | `event-bus.ts` |

Paths are relative to `$PI_CODING_AGENT_ROOT/examples/extensions/`.
