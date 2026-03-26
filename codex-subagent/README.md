# codex-subagent

Skills for dispatching parallel tasks to Codex CLI subagents.

## Skills

| Name | Description | Install | Last updated (UTC) |
|---|---|---|---|
| `codex-subagent` | Dispatch parallel tasks to Codex CLI subagents to save Claude Code tokens. Accepts explicit task descriptions, auto-selects sandbox (read-only vs workspace-write) and reasoning effort (high vs xhigh) based on task type, and collects structured results with durable artifacts. | `npx skills install HenryQW/skills codex-subagent -a codex -a claude-code -y` | 2026-03-26 00:24 |
