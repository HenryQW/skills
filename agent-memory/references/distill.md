# Distill Reference

Distill mode turns temporary task notes into durable memory.

## Write Memory For

- accepted decisions and why they exist
- root causes future agents might rediscover
- repeated repo/worktree traps
- mistakes to avoid
- rules and coding style
- library or framework preferences
- non-obvious commands or validation paths
- architecture context that survived review or merge readiness

## Do Not Write Memory For

- ordinary todo progress
- transient branch state
- passing/failing checks with no reusable lesson
- one-off typos or mistakes
- duplicate context already present in `Agent/Memory`

## Memory Shape

Use the project convention if one exists. Otherwise:

```md
# Title

Summary: One sentence.
Keywords: keyword, keyword

## Context

What happened and why.

## Current Decision

What is durable now.

## Use Next Time

What future agents should check before repeating the discovery.
```
