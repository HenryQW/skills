---
name: multica-cli
description: Operate an existing Multica workspace from the CLI. Use for issues, agents, skills, squads, projects, autopilots, daemon runtimes, repositories, and attachments.
---

# Multica CLI

Assume authentication and workspace selection are already configured. Use
`multica <command> --help` before inventing flags. Prefer `--output json` when
results will be parsed. Resolve and inspect targets before destructive actions.

## Issues

```sh
multica issue list
multica issue get <id>
multica issue search <query>
multica issue create --title "..."
multica issue update <id> ...
multica issue assign <id> --to <agent-or-squad>
multica issue status <id> <status>
multica issue children <id>
multica issue pull-requests <id>
multica issue runs <id>
multica issue run-messages <task-id>
multica issue usage <id>
multica issue rerun <id>
multica issue cancel-task <task-id>
multica issue comment <id> ...
multica issue comment resolve|unresolve <comment-id>
multica issue subscriber <id> ...
multica issue metadata <id> ...
multica issue label <id> ...
```

Issue keys such as `MUL-123` and UUIDs are accepted where an issue ID is
required.

## Agents and skills

```sh
multica agent list
multica agent get <id>
multica agent create ...
multica agent update <id> ...
multica agent archive|restore <id>
multica agent tasks <id>
multica agent avatar <id> ...
multica agent env get|set <id> ...
multica agent skills ...

multica skill list|get|create|update|delete ...
multica skill import ...
multica skill files ...
```

Multica does not shell-expand custom environment values or arguments. Use
resolved absolute paths, never `$HOME` or `~`. Use
`multica agent env set <id> --custom-env-stdin` for environment replacement.
Pass CLI arguments as a JSON string array through `--custom-args`.

## Squads

```sh
multica squad list
multica squad get <id>
multica squad create --name "..." --leader <agent>
multica squad update <id> ...
multica squad delete <id>
multica squad member list <id>
multica squad member add|remove|set-role <id> ...
multica squad activity <issue-id> action|no_action|failed --reason "..."
```

Deleting a squad archives it. Inspect membership and assigned work first.

## Projects, labels, and autopilots

```sh
multica project list|get|create|update|delete|status ...
multica label list|create|update|delete ...

multica autopilot list|get|create|update|delete ...
multica autopilot runs <id>
multica autopilot trigger <id>
multica autopilot trigger-add|trigger-update|trigger-delete <id> ...
multica autopilot trigger-rotate-url <id> <trigger-id>
```

## Daemon and runtimes

```sh
multica daemon start|stop|restart|status|logs
multica runtime list
multica runtime usage
multica runtime activity
multica runtime update <id> ...
multica runtime delete <id> [--cascade]
multica runtime profile ...
```

## Supporting operations

```sh
multica workspace list|get ...
multica workspace member list
multica workspace update <id> ...
multica repo checkout <url>
multica attachment download <id>
```
