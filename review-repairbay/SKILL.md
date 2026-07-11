---
name: review-repairbay
description: Inspect or address actionable GitHub pull request review feedback. Use when the user wants to inspect unresolved review threads, fix selected feedback, or clear all actionable comments on a PR. Use `gh` and the bundled GraphQL script whenever thread-level state, resolution status, or inline review context matters.
---

# Review Repairbay

Use this skill when the user wants to work through requested changes on a GitHub pull request. Treat thread-aware review data as a `gh api graphql` problem because flat comment surfaces do not preserve full review-thread state.

## Memory Boundary

- When the user invokes `review-repairbay` directly for `fix-selected` or `clear-all`, call `$agent-memory load` before resolving the PR and `$agent-memory distill` immediately before the final `status=PASS|BLOCKED|PENDING` line.
- For `inspect-only`, skip both memory calls so the workflow remains read-only.
- When a caller such as Shipyard owns the memory boundary, skip both calls and preserve `.context/decisions.jsonl` for that caller.
- Capture only an accepted durable review decision, repository rule, or reusable root cause. Do not capture comment text, thread state, review IDs, or routine fixes.
- Memory failure must not change the repair status.

## Workflow

1. Select the intent from the request.
   - `inspect-only`: read, cluster, and report; do not edit files or write to GitHub.
   - `fix-selected`: address only the threads the user selected and validate locally. If no selection was provided, present numbered actionable threads and ask which to address. Do not write to GitHub unless requested.
   - `clear-all`: an explicit request to clear, resolve, or address every unresolved review comment authorizes scoped local fixes plus thread replies, resolutions, and re-fetches. Do not perform unrelated GitHub writes, and honor any restriction the user places on GitHub writes.
2. Resolve the PR.
   - Inputs: `repo_slug` is `OWNER/REPO`; `pr` is a PR number or GitHub pull request URL.
   - If `pr` is a URL, derive `repo_slug` and the PR number from it.
   - If `pr` is a number, require `repo_slug` and pass it to `scripts/fetch_comments.py` as `--repo`.
   - If neither is provided, use the current branch PR with `gh pr view --json number,url`.
3. Inspect review context with thread-aware reads.
   - Use the bundled script whenever the task depends on unresolved review threads, inline review locations, or resolution state:
     - `python "<path-to-skill>/scripts/fetch_comments.py" --repo OWNER/REPO --pr NUMBER`
     - `python "<path-to-skill>/scripts/fetch_comments.py" --pr https://github.com/OWNER/REPO/pull/NUMBER`
   - That script fetches `reviewThreads`, `isResolved`, `isOutdated`, and file and line anchors.
   - Use flat PR comment reads only for lightweight top-level PR comment summaries.
4. Cluster actionable review threads.
   - Group comments by file or behavior area.
   - Separate actionable change requests from informational comments, approvals, already-resolved threads, and duplicates.
5. Implement only the authorized scope.
   - Keep each code change traceable back to the thread or feedback cluster it addresses.
   - If a comment calls for explanation rather than code, draft the response rather than forcing a code change.
   - Ask only when a thread is ambiguous, conflicts with another request, or requires a material product decision.
   - Run validation proportionate to the changed behavior.
   - For `clear-all`, reply to or resolve each addressed thread as appropriate, then re-fetch thread state until no unresolved actionable threads remain.
6. Summarize the result.
   - List which threads were addressed, which were intentionally left open, and what tests or checks support the change.

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

- `inspect-only` and `fix-selected` do not authorize GitHub writes. `clear-all` authorizes only the scoped thread replies and resolutions needed to clear the actionable feedback; submitting a review or other external writes still requires explicit authorization.
- If review comments conflict with each other or would cause a behavioral regression, surface the tradeoff before making changes.
- If a comment is ambiguous, ask for clarification or draft a proposed response instead of guessing.
- Do not treat flat PR comments as a complete representation of review-thread state.
- If `gh` hits auth or rate-limit issues mid-run, ask the user to re-authenticate and retry.

## Fallback

If `gh` cannot resolve the PR cleanly, tell the user whether the blocker is missing repository scope, missing PR context, or CLI authentication, then ask for the missing repo or PR identifier or for a refreshed `gh` login.
