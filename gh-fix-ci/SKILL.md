---
name: gh-fix-ci
description: Fix actionable GitHub PR review comments or CI feedback end-to-end. Use when Codex must inspect unresolved review threads or failing checks, implement actionable fixes, commit and push those fixes, resolve fixed threads, reply and resolve non-actionable threads, and add or re-add Copilot as reviewer after any pushed commit.
---

# GitHub Fix CI And Review Comments

Use this skill when the user asks to fix GitHub PR feedback, CI failures, unresolved review comments, requested changes, or a similar PR cleanup queue where GitHub write-back is expected.

Treat the durable workflow as:

`fix actionable -> commit + push -> resolve fixed threads -> reply to non-actionable with reason -> resolve -> add or re-add Copilot reviewer if anything was committed`

## 1) Resolve PR Context

- If the user provides a repository and PR number or URL, use that directly.
- If the request is about the current branch PR, use local git context plus `gh auth status` and `gh pr view --json number,url,headRefName,baseRefName`.
- If CLI authentication fails, ask the user to refresh `gh` auth before making GitHub writes.

## 2) Fetch Source Of Truth

- Fetch thread-aware review data with GraphQL or an existing repository script that returns `reviewThreads`, `isResolved`, `isOutdated`, file anchors, line anchors, and comment bodies.
- Fetch failing checks with `gh pr checks` and, when needed, inspect failing GitHub Actions logs before editing.
- Do not treat flat PR comments as complete review-thread state.
- Ignore already-resolved review threads unless the user asks to audit them.

## 3) Classify Feedback

For each unresolved thread or failing check, classify it as:

- `actionable`: a concrete code, test, config, docs, or CI fix is needed.
- `non-actionable`: already fixed by current code, outdated, incorrect, duplicate, conflicting with a stronger requirement, or impossible without changing the requested scope.
- `ambiguous`: not enough information to safely act.

If the user says to fix all feedback, proceed with all unresolved actionable items. For ambiguous items, either clarify with the user or leave a specific GitHub reply explaining the blocker when the user's directive is to clear every thread.

## 4) Fix Actionable Items

- Keep each change traceable to the review thread or failing check it addresses.
- Preserve unrelated user changes and do not bundle opportunistic cleanup.
- Add or update focused tests when the fix changes behavior.
- Run verification appropriate to the touched code and the failing checks.
- If verification cannot run, record the exact blocker and include it in the PR reply or final summary.

## 5) Commit And Push

If files changed:

- Inspect the diff and stage only the intended files.
- Commit with a scoped Conventional Commit message.
- Push the branch.
- Record the pushed commit SHA for later replies.

Do not resolve fixed review threads before the commit is pushed unless the user explicitly directs otherwise.

## 6) Resolve Threads

Resolve threads after the pushed commit when code changed. If no files changed because every selected thread is non-actionable, reply and resolve those non-actionable threads immediately after classification.

- For each actionable thread fixed by the commit, reply with a short note that names the fix and, when useful, the commit SHA or verification run.
- Resolve that review thread.
- For each non-actionable thread, reply with the concrete reason it is not actionable, then resolve the thread.
- For ambiguous threads that cannot be safely resolved, leave them unresolved and report exactly what is needed, unless the user's instruction explicitly says to clear them with a blocker reply.
- Re-fetch review threads after resolving and continue until the selected thread set is closed or a real blocker remains.

## 7) Add Or Re-Add Copilot Reviewer

If any commit was pushed during this workflow, add or re-add Copilot as reviewer after the push and thread updates:

```bash
gh pr edit <PR number> --add-reviewer "copilot-pull-request-reviewer"
```

If the command succeeds without error, assume Copilot was added. Do not spend extra time verifying reviewer state unless the command fails or the user asks.

## 8) Report Results

Final response must include:

- PR URL or number.
- Pushed commit SHA, if any.
- Threads fixed and resolved.
- Threads replied as non-actionable and resolved.
- Any unresolved blockers.
- Checks or verification actually run.

## Write Policy

This skill is intentionally write-capable. When it triggers, the default expectation is to commit, push, reply, resolve, and refresh Copilot reviewer when those actions are needed to complete the PR cleanup. Stop only when GitHub authentication, missing PR context, conflicting requirements, or unsafe ambiguity prevents correct action.
