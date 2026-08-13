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
| Modify prompt or inject context | `before_agent_start`, `context` | `pirate.ts`, `plan-mode/index.ts` |
| Track runs and turns | `agent_start/end`, `turn_start/end` | `status-line.ts`, `titlebar-spinner.ts` |
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

- Factory may run without a session. Register handlers, tools, commands, flags,
  and providers there; start long-lived resources at `session_start` or on first
  use. Make `session_shutdown` cleanup idempotent.
- Module variables are caches, not durable state. Store branch-aware tool state
  in tool-result `details`; store durable non-LLM extension data with
  `pi.appendEntry()`. Reconstruct from `ctx.sessionManager.getBranch()` on
  `session_start` and `session_tree`.
- Before-events cancel explicitly with `{ cancel: true }`. Tool interception
  blocks explicitly with `{ block: true, reason }`. For dangerous actions with
  no UI, fail closed rather than silently allow.
- Input handlers return `continue`, `transform`, or `handled`. Check
  `event.streamingBehavior`; skip slow preprocessing for steering input.
- `before_agent_start` changes next run only. Use `context` to filter or replace
  messages sent to model; do not mutate persisted session history accidentally.
- Custom compaction must honor provided abort signal and return nothing to use
  default compaction. Trigger compaction from stable lifecycle boundary, avoid
  duplicate calls, and expose failures through `onError`.
