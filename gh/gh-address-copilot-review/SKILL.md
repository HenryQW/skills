---
name: gh-address-copilot-review
description: Handle GitHub PR review comments when comments are provided by the user as context. Use when Codex must evaluate comments one by one, classify each as actionable or non-actionable or needs clarification, implement only necessary fixes, keep changes scoped per comment, run validation, avoid intermediate pushes, perform one final push for the full batch, resolve addressed threads, respond to rejected comments with rationale, and re-request Copilot reviewer exactly once at the end via gh-assign-copilot-reviewer.
---

# GitHub Copilot Review Handler

## Overview

Use this skill to process review feedback on an existing PR with a strict,
repeatable sequence.

Optimize for correctness and review signal quality, not blind compliance.

Treat each review thread as an independent decision.

Refer `gh-cli` skill for available GitHub interactions, when needed.
Refer `gh-assign-copilot-reviewer` skill for assigning or re-requesting Copilot reviewer.

## Preconditions

- Treat user-provided review comments as the only source of thread/comment input.

- Do not fetch review comments from GitHub using `gh` or API calls.

- If comments are missing or incomplete, ask the user to provide all relevant
  review threads before processing.

- Verify `gh` authentication before PR operations:

```bash
gh auth status
```

- Confirm the active branch is the PR branch being updated.

- Create or update a local tracker file (for example,
  `.context/review-batch-status.md`) to record thread status:
  `pending`, `addressed`, `rejected-with-rationale`, `needs-clarification`.

## Batch Workflow

### 1. Ingest user-provided review threads

Use the review comments passed by the user in task context as the authoritative
input.

Normalize comments into a numbered local tracker with thread identifiers (if
provided), raw comment text, and an initial status of `pending`.

### 2. Handle one thread at a time

For each thread, classify it first:

- `Actionable`: requires code, docs, or test updates.
- `Non-actionable`: incorrect, preference-only, already covered, or out of
  scope.
- `Needs clarification`: intent is ambiguous and correctness could be affected.

Do not combine multiple threads into a single decision.

Update the tracker immediately after classification.

### 3. If actionable, execute full fix cycle

Apply only the changes needed for that one thread.

Keep the fix scoped and reviewable.

Update tests and documentation when behavior or contracts change.

Run validation after each actionable fix or small grouped set of related fixes.

Run stricter/full checks before final push if required by the repo.

Create focused local commits while iterating.

Do not push yet.

Mark thread status as `addressed` in the local tracker.

### 4. If non-actionable, document rationale

Write a short technical rationale explaining why no code change is needed.

Reference existing behavior, tests, or constraints when possible.

Mark tracker status as `rejected-with-rationale`.

### 5. If clarification is needed

Ask one precise question that unblocks implementation.

Do not guess when safety or correctness is uncertain.

Mark tracker status as `needs-clarification`.

## Finalization Rules

Only finalize when all threads are either `addressed` or
`rejected-with-rationale`.

Do not finalize while any thread remains `pending` or `needs-clarification`.

When the batch is complete, execute exactly one push for all local commits.

After the push:

1. Resolve addressed threads in GitHub.
2. Reply to non-actionable threads with rationale.
3. Re-request Copilot review exactly once at the end by invoking
   `gh-assign-copilot-reviewer` for the current `<PR_NUMBER>` with the
   "reviews addressed on existing PR" scenario.

Never invoke `gh-assign-copilot-reviewer` before steps 1 and 2 are complete
for all threads.

Never push more than once per review batch.

## Output Contract

When reporting progress, provide:

- A numbered list of threads and current classification.
- Which actionable fixes were implemented.
- Which comments were rejected and why.
- Validation commands that were run and their outcomes.
- Confirmation that push count is one for the batch.
- Confirmation that Copilot was re-requested once, only at the end, via
  `gh-assign-copilot-reviewer`.
