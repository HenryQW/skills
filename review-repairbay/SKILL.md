---
name: review-repairbay
description: Inspect or address actionable GitHub pull request review feedback. Use when the user wants to inspect unresolved review threads, fix selected feedback, or clear all actionable comments on a PR. Use `gh` and the bundled GraphQL script whenever thread-level state, resolution status, or inline review context matters.
---

# Review Repairbay

Use this skill when the user wants to work through requested changes on a GitHub pull request. Treat thread-aware review data as a `gh api graphql` problem because flat comment surfaces do not preserve full review-thread state.

## Memory Boundary

For direct `fix-selected` or `clear-all`, call `$agent-memory load` before resolving the PR and `$agent-memory distill` immediately before the final `status=PASS|BLOCKED|PENDING` line. `inspect-only` and callers such as Shipyard skip both and preserve `.context/decisions.jsonl` for the caller. Capture only accepted durable review decisions, repository rules, or reusable root causes—not comment text, thread state, review IDs, or routine fixes. Memory failure must not change repair status.

## Workflow

1. Select the intent: `inspect-only` reads, clusters, and reports without edits or GitHub writes; `fix-selected` addresses only selected threads and asks for a selection when none is provided; `clear-all` authorizes scoped local fixes, thread replies/resolutions, and re-fetches for every unresolved comment.
2. Resolve `repo_slug` (`OWNER/REPO`) and `pr` (number or URL): derive both from a URL; require and pass `--repo` for a number; otherwise use the current branch PR via `gh pr view --json number,url`.
3. Use `python "<path-to-skill>/scripts/fetch_comments.py" --repo OWNER/REPO --pr NUMBER` (or a PR URL) whenever unresolved threads, inline locations, or resolution state matter. It fetches `reviewThreads`, `isResolved`, `isOutdated`, and file/line anchors; use flat reads only for lightweight top-level summaries.
4. Group threads by file or behavior and separate actionable requests from informational comments, approvals, resolved threads, and duplicates.
5. Keep every change traceable to its thread/cluster; draft explanations instead of forcing code changes, ask only for ambiguity/conflicts/material product decisions, and validate proportionately. For `clear-all`, reply/resolve each addressed thread and re-fetch until no unresolved actionable threads remain.
6. List addressed and intentionally open threads plus supporting checks.

## Output

End with one compact status line:

```text
status=PASS|BLOCKED|PENDING artifacts=<path-or-none> summary=<one line>
```

- `PASS` for `inspect-only`: the thread-aware report is complete and nothing was mutated.
- `PASS` for `fix-selected`: every selected thread is addressed locally and relevant validation passes; requested GitHub writes, if any, are complete.
- `PASS` for `clear-all`: every unresolved actionable thread is addressed, relevant validation passes, and a final re-fetch reports zero unresolved actionable threads.
- `BLOCKED`: a thread is ambiguous, conflicting, requires a product decision, or GitHub access is unavailable.
- `PENDING`: a requested review-thread write or re-fetch is still in progress.

## Write Safety

- `inspect-only` and `fix-selected` do not authorize GitHub writes. `clear-all` authorizes only scoped replies/resolutions needed to clear actionable feedback; submitting a review or other external writes still requires explicit authorization and all user restrictions apply.
- If review comments conflict with each other or would cause a behavioral regression, surface the tradeoff before making changes.
- If a comment is ambiguous, ask for clarification or draft a proposed response instead of guessing.
- Do not treat flat PR comments as a complete representation of review-thread state.
- If `gh` hits auth or rate-limit issues mid-run, ask the user to re-authenticate and retry.

## Fallback

If `gh` cannot resolve the PR cleanly, tell the user whether the blocker is missing repository scope, missing PR context, or CLI authentication, then ask for the missing repo or PR identifier or for a refreshed `gh` login.
