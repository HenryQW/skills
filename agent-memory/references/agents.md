# AGENTS.md Memory Snippets

Setup mode uses these exact snippets. Keep placeholders intact; the setup script replaces them.

## Context and precedence item

```md
  - `{memory_index_ref}`
```

## Execution item

```md
- When `$agent-memory` is invoked or progress distillation is requested, use `.context/progress.md` as the temporary source and write or update real markdown memory under `{memory_dir_ref}/` only when it contains durable context future agents would otherwise rediscover. Memory can include history, mistakes to avoid, rules, coding style, library preferences, and validation paths. Skip routine progress, duplicate lessons, and one-off mistakes.
```
