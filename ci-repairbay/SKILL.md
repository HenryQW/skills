---
name: "ci-repairbay"
description: "Use when a user asks to inspect, diagnose, or fix failing GitHub PR checks that run in GitHub Actions. Inspection requests stay read-only; explicit fix requests authorize scoped local changes and validation."
---


# CI Repairbay

## Overview

Use this skill when the task is specifically about failing GitHub Actions checks on a pull request. Use `gh` for PR metadata, changed files, checks, and logs.

- For inspect, diagnose, explain, or review requests, inspect and report without modifying files or triggering external writes.
- For explicit fix requests, implement the smallest scoped local fix and run relevant non-destructive validation without asking again.
- Require confirmation before external writes, destructive actions, or a material expansion beyond the requested scope unless the user already authorized that action.

## Memory Boundary

- When the user invokes `ci-repairbay` directly, call `$agent-memory load` before resolving the PR and `$agent-memory distill` immediately before the final `status=PASS|BLOCKED|PENDING` line.
- When a caller such as Shipyard owns the memory boundary, skip both calls and preserve `.context/decisions.jsonl` for that caller.
- Capture only a confirmed reusable CI root cause, repository guardrail, or durable fix decision. Do not capture check status, logs, run IDs, or flaky/transient failures.
- Memory failure must not change the repair status.

## Inputs

- `repo_path`: path inside the repo (default `.`); pass this to the script as `--repo`
- `pr`: PR number or URL (optional; defaults to current branch PR)

## Quick start

- `python "<path-to-skill>/scripts/inspect_pr_checks.py" --repo "." --pr "<number-or-url>"` (add `--json` for machine-friendly output)

## Workflow

1. Resolve the PR.
   - Inputs: `repo_path` is a local path inside the target repository; `pr` is a PR number or GitHub pull request URL.
   - If `pr` is a URL, use that URL directly with `gh`.
   - If `pr` is a number, run from the target repository or pass the local path with `--repo`.
   - If neither is provided, use the current branch PR with `gh pr view --json number,url`.
   - Fetch PR metadata and changed files with `gh pr view`.
2. Inspect failing checks (GitHub Actions only).
   - Run the bundled script from Quick start; it handles `gh` field drift and job-log fallbacks.
3. Scope non-GitHub Actions checks.
   - If the check URL is not a GitHub Actions run, label it as external and only report the URL.
   - Do not attempt Buildkite or other providers; keep the workflow lean.
4. Summarize failures for the user.
   - Provide the failing check name, run URL (if any), and a concise log snippet.
   - Call out missing logs explicitly and do not over-claim certainty.
   - For inspect or diagnose requests, stop after this report.
5. For explicit fix requests, apply the smallest local change tied directly to the observed root cause.
   - Run the most relevant non-destructive local verification available.
   - Ask before pushing, triggering a rerun, mutating the PR, taking a destructive action, or expanding beyond the requested scope unless that action was already authorized.
6. Recheck status and summarize residual risk.
   - Rerun the bundled inspection script or the specific failed local check; do not also run `gh pr checks` when the script already returned current PR check state.
   - Report what is still unverified, what may still be flaky, and whether any failing checks were external and therefore not actionable here.

## Output

End with one compact status line:

```text
status=PASS|BLOCKED|PENDING artifacts=<path-or-none> summary=<one line>
```

- `PASS`: the requested diagnosis is complete, GitHub Actions blockers are fixed, or only waived/external non-actionable checks remain.
- `BLOCKED`: a requested fix needs additional authorization, missing credentials, missing logs, or a non-GitHub provider.
- `PENDING`: a check rerun was triggered or is still running.

## Bundled Resources

### scripts/inspect_pr_checks.py

Fetch failing PR checks, pull GitHub Actions logs, and extract a failure snippet. Exits non-zero when failures remain so it can be used in automation.

## Guardrails

- Treat non-GitHub Actions providers as report-only unless the user explicitly wants a separate investigation path.
- If the failure is clearly unrelated to the local diff, report it and ask before expanding the fix scope.
