---
name: codex-subagent
description: Dispatch one or more tasks to Codex CLI subagents to save Claude Code tokens. Accepts explicit task descriptions, auto-selects sandbox (read-only vs workspace-write) and reasoning effort (high vs xhigh) based on task type, and collects structured results with durable artifacts.
---

# Codex Subagent

Dispatch one or more tasks to Codex CLI subagents. Multiple tasks run in parallel. Collect structured results with durable artifacts.

## When to Use

- The user or a calling skill needs to offload tasks to Codex to save Claude Code tokens.
- For 2+ independent tasks, parallel dispatch is the primary value.

Do NOT use this skill when:

- Tasks depend on each other's output (run them sequentially instead).

## Task Types (Reference)

`run_batch.py` is the single source of truth for this mapping. This table is informational only.

| Type | Sandbox | Effort |
|---|---|---|
| `review` | read-only | high |
| `analyze` | read-only | high |
| `search` | read-only | high |
| `document` | read-only | high |
| `implement` | workspace-write | xhigh |
| `refactor` | workspace-write | xhigh |
| `debug` | workspace-write | xhigh |
| `architect` | workspace-write | xhigh |

Unknown types default to read-only / high.

## Construct the Task Manifest

1. Receive explicit task descriptions from the user or calling skill.
2. Do NOT invent tasks beyond what was described.
3. Build a manifest JSON with a `tasks` array. Each task requires:
   - `id` -- unique string identifier using only letters, numbers, `.`, `_`, or `-`
   - `type` -- one of the canonical types above
   - `prompt` -- full task instruction string
   - `cwd` -- working directory relative to git root and staying inside the repo (usually `"."`)

Example manifest:

```json
{
  "tasks": [
    {
      "id": "lint-config",
      "type": "review",
      "prompt": "Review the ESLint configuration for deprecated rules and report findings.",
      "cwd": "."
    },
    {
      "id": "add-retry-logic",
      "type": "implement",
      "prompt": "Add exponential backoff retry logic to src/api/client.ts for transient HTTP errors.",
      "cwd": "."
    }
  ]
}
```

## Execution Flow

1. Create `.context/codex-subagent/` under the repo root if it does not exist.
2. Write the manifest to `.context/codex-subagent/manifest.json`.
3. Run the runner:

```bash
python "<skill-install-path>/codex-subagent/scripts/run_batch.py" \
  --manifest ".context/codex-subagent/manifest.json" \
  --run-id "$(date +%Y%m%d-%H%M%S)"
```

To specify a model, add `--model <model>`.

`--run-id` must also use only letters, numbers, `.`, `_`, or `-`.

4. The runner prints summary JSON to stdout.

## Monitoring Long-Running Tasks

Every 5 minutes while the runner is executing, check `.context/codex-subagent/<run-id>/` for task progress:

- Task directory has only `prompt.txt` -- still launching.
- Task directory has `prompt.txt` + `pid` -- currently running.
- Task directory has `meta.json` (no `pid`) -- completed.

If a read-only task has been running >15 minutes or a workspace-write task >30 minutes, read the `pid` file and consider killing it with `kill <pid>`.

## Presenting Results

1. Read summary JSON from runner stdout.
2. If any task has `truncated: true`, read the full output from `.context/codex-subagent/<run-id>/<task-id>/stdout.txt`.
3. Present results as concatenated per-task outputs with task ID headers.
4. If any task failed, report which ones and offer to retry.

## Write Isolation Warning

When dispatching multiple workspace-write tasks, the caller must ensure non-overlapping file sets. The runner only warns when multiple workspace-write tasks share the same `cwd`; it does not detect overlapping file sets within a directory and does not prevent concurrent writes. If isolation cannot be guaranteed, use distinct `cwd` values or run the tasks sequentially instead.

## Exit Codes

| Code | Meaning |
|---|---|
| 0 | All tasks succeeded |
| 1 | One or more tasks failed (partial results available) |
| 2 | Runner error (bad manifest, missing codex, auth failure) |

## Error Recovery

- Exit code 2: verify `codex` is installed and authenticated (`codex login status`).
- Individual task failure: check stderr in `.context/codex-subagent/<run-id>/<task-id>/stderr.txt`.
