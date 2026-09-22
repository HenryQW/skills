# Lifecycle and State

Navigation aid distilled from published examples. Verify event payloads and
return types in installed `docs/extensions.md` before editing code.

## Event routing

| Need | Event or API | Published examples |
|---|---|---|
| Resolve cwd-bound config and start resources | `session_start` | `file-trigger.ts`, `ssh.ts` |
| Release timers, watchers, processes, sockets | `session_shutdown` | `mac-system-theme.ts`, `sandbox/index.ts` |
| Guard clear, switch, fork, tree, or compact | `session_before_*` | `confirm-destructive.ts`, `dirty-repo-guard.ts` |
| Restore branch-dependent state | `session_start`, `session_tree` | `todo.ts`, `tools.ts` |
| Modify prompt or inject context | `before_agent_start`, `context`, `context_with_system` | `pirate.ts`, `plan-mode/index.ts` |
| Track runs and turns | `agent_start/end`, `turn_start/end` | `status-line.ts`, `titlebar-spinner.ts` |
| Act before final continuation or observe full settlement | `agent_before_settle`, `agent_settled` | `git-checkpoint.ts`, `notify.ts` |
| Observe failed or aborted compaction | `session_compact_failed` | Verify payload in installed types |
| Inspect or change tool traffic | `tool_call`, `tool_result` | `permission-gate.ts`, `git-checkpoint.ts` |
| Replace shell execution | `user_bash` | `interactive-shell.ts`, `ssh.ts` |
| Handle or transform user input | `input` | `input-transform.ts`, `input-transform-streaming.ts` |
| React to model changes | `model_select`, `thinking_level_select` | `model-status.ts` |
| Customize compaction | `session_before_compact`, `ctx.compact()` | `custom-compaction.ts`, `trigger-compact.ts` |
| Inspect provider traffic | provider request/response hooks | `provider-payload.ts` |
| Add runtime resources | `resources_discover` | `dynamic-resources/index.ts` |
| Gate project-local startup | `project_trust` | `project-trust.ts` |

Paths are relative to `$PI_CODING_AGENT_ROOT/examples/extensions/`.

## Durable patterns

- Factory may run without a session and may be async. Register handlers, tools,
  commands, flags, and providers there; start long-lived resources at
  `session_start` or on first use. Make `session_shutdown` cleanup idempotent,
  including on reload or session replacement.
- Module variables are caches, not durable state. Store branch-aware tool state
  in tool-result `details`; store durable non-LLM extension data with
  `pi.appendEntry()`. Reconstruct from `ctx.sessionManager.getBranch()` on
  `session_start` and `session_tree`.
- Before-events cancel explicitly with `{ cancel: true }`. Tool interception
  blocks explicitly with `{ block: true, reason }`. For dangerous actions with
  no UI, fail closed rather than silently allow.
- Input handlers return `continue`, `transform`, or `handled`. Check
  `event.streamingBehavior`; skip slow preprocessing for steering input.
- Prefer structured `systemPromptOptions` changes in `before_agent_start`;
  replacing `systemPrompt` forces the full prompt for that run. `context` changes
  conversation messages for one request, not prompt/tool system messages. Use
  `context_with_system` only when owning the full transcript; preserve its
  leading system message. Do not mutate persisted history accidentally.
- `turn_end` and `agent_before_settle` can append boundary entries and request
  continuation; guard against loops. `agent_end` is not guaranteed final because
  recovery, compaction, or queued work can follow. `agent_settled` is final and
  notification-only. Check event types for valid boundary entries and outcomes.
- Custom compaction must honor its abort signal and return nothing to use
  default compaction. Trigger compaction from a stable lifecycle boundary, avoid
  duplicate calls, and expose failures through `onError` or
  `session_compact_failed` as appropriate.
