---
name: review-repairbay
description: Address actionable GitHub pull request review feedback. Use when the user wants to inspect unresolved review threads, requested changes, or inline review comments on a PR, then implement selected fixes. Use `gh` and the bundled GraphQL script whenever thread-level state, resolution status, or inline review context matters.
---

# Review Repairbay

Use this skill when the user wants to work through requested changes on a GitHub pull request. Treat thread-aware review data as a `gh api graphql` problem because flat comment surfaces do not preserve full review-thread state.

## Workflow

1. Resolve the PR.
   - Inputs: `repo_slug` is `OWNER/REPO`; `pr` is a PR number or GitHub pull request URL.
   - If `pr` is a URL, derive `repo_slug` and the PR number from it.
   - If `pr` is a number, require `repo_slug` and pass it to `scripts/fetch_comments.py` as `--repo`.
   - If neither is provided, use the current branch PR with `gh pr view --json number,url`.
2. Inspect review context with thread-aware reads.
   - Use the bundled script whenever the task depends on unresolved review threads, inline review locations, or resolution state:
     - `python "<path-to-skill>/scripts/fetch_comments.py" --repo OWNER/REPO --pr NUMBER`
     - `python "<path-to-skill>/scripts/fetch_comments.py" --pr https://github.com/OWNER/REPO/pull/NUMBER`
   - That script fetches `reviewThreads`, `isResolved`, `isOutdated`, and file and line anchors.
   - Use flat PR comment reads only for lightweight top-level PR comment summaries.
3. Cluster actionable review threads.
   - Group comments by file or behavior area.
   - Separate actionable change requests from informational comments, approvals, already-resolved threads, and duplicates.
4. Confirm scope before editing.
   - Present numbered actionable threads with a one-line summary of the required change.
   - If the user did not ask to fix everything, ask which threads to address.
   - If the user asks to fix everything, interpret that as all unresolved actionable threads and call out anything ambiguous.
5. Implement the selected fixes locally.
   - Keep each code change traceable back to the thread or feedback cluster it addresses.
   - If a comment calls for explanation rather than code, draft the response rather than forcing a code change.
6. Summarize the result.
   - List which threads were addressed, which were intentionally left open, and what tests or checks support the change.

## Write Safety

- Do not reply on GitHub, resolve review threads, or submit a review unless the user explicitly asks for that write action.
- If review comments conflict with each other or would cause a behavioral regression, surface the tradeoff before making changes.
- If a comment is ambiguous, ask for clarification or draft a proposed response instead of guessing.
- Do not treat flat PR comments as a complete representation of review-thread state.
- If `gh` hits auth or rate-limit issues mid-run, ask the user to re-authenticate and retry.

## Fallback

If `gh` cannot resolve the PR cleanly, tell the user whether the blocker is missing repository scope, missing PR context, or CLI authentication, then ask for the missing repo or PR identifier or for a refreshed `gh` login.
