---
name: "ci-repairbay"
description: "Use when a user asks to inspect, diagnose, or fix failing GitHub PR checks that run in GitHub Actions. Inspection requests stay read-only; explicit fix requests authorize scoped local changes and validation."
---


# CI Repairbay

## Overview

Use this skill for failing GitHub Actions checks on a pull request. Its bundled
script uses `github-adapter` for PR context, checks, and logs.

- Inspect, diagnose, explain, and review requests are read-only.
- Explicit fix requests authorize the smallest scoped local fix and relevant
  non-destructive validation.
- Require confirmation for external writes, destructive actions, or material
  scope expansion unless already authorized.

## Memory Boundary

- When the user invokes `ci-repairbay` directly, call `$agent-memory load` before resolving the PR and `$agent-memory distill` immediately before the final `status=PASS|BLOCKED|PENDING` line.
- When a caller such as Shipyard owns the memory boundary, skip both calls and preserve `.context/decisions.jsonl` for that caller.
- Capture only a confirmed reusable CI root cause, repository guardrail, or durable fix decision. Do not capture check status, logs, run IDs, or flaky/transient failures.
- Memory failure must not change the repair status.

## Inputs

- `repo_path`: target-repository path (default `.`); pass as `--repo`
- `pr`: optional PR number or URL; defaults to the current-branch PR

## Quick start

- `python "<path-to-skill>/scripts/inspect_pr_checks.py" --repo "." --pr "<number-or-url>"` (add `--json`; add `--log-tail` only when the failure snippet is insufficient)

## Workflow

1. Resolve the PR: use a URL directly, resolve a number in `repo_path`, or use
   the current-branch PR when omitted. Fetch PR metadata and changed files.
2. Inspect failing GitHub Actions checks.
   - Run the bundled script from Quick start; it handles field drift and job-log fallbacks through `github-adapter`.
3. Scope non-GitHub Actions checks.
   - If the check URL is not a GitHub Actions run, label it as external and only report the URL.
   - Do not attempt Buildkite or other providers; keep the workflow lean.
4. Summarize failures for the user.
   - Provide the failing check name, run URL (if any), and a concise log snippet.
   - Call out missing logs explicitly and do not over-claim certainty.
   - For inspect or diagnose requests, stop after this report.
5. For an explicit fix request, apply the smallest local change tied to the
   observed root cause and run the most relevant non-destructive verification.
6. Recheck status and summarize residual risk.
   - Rerun the bundled script or failed local check; do not also run `gh pr checks`
     when the script returned current PR state.
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
