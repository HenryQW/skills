---
name: "ci-repairbay"
description: "Use when a user asks to debug or fix failing GitHub PR checks that run in GitHub Actions. Use `gh` for PR resolution, Actions check inspection, and log inspection before implementing any approved fix."
---


# CI Repairbay

## Overview

Use this skill when the task is specifically about failing GitHub Actions checks on a pull request. Use `gh` for PR metadata, changed files, checks, and logs.
- Summarize the root cause first, propose a focused fix plan, and implement only after explicit approval.

## Inputs

- `repo_path`: path inside the repo (default `.`); pass this to the script as `--repo`
- `pr`: PR number or URL (optional; defaults to current branch PR)

## Quick start

- `python "<path-to-skill>/scripts/inspect_pr_checks.py" --repo "." --pr "<number-or-url>"`
- Add `--json` if you want machine-friendly output for summarization.

## Workflow

1. Resolve the PR.
   - Inputs: `repo_path` is a local path inside the target repository; `pr` is a PR number or GitHub pull request URL.
   - If `pr` is a URL, use that URL directly with `gh`.
   - If `pr` is a number, run from the target repository or pass the local path with `--repo`.
   - If neither is provided, use the current branch PR with `gh pr view --json number,url`.
   - Fetch PR metadata and changed files with `gh pr view`.
2. Inspect failing checks (GitHub Actions only).
   - Preferred: run the bundled script (handles gh field drift and job-log fallbacks):
     - `python "<path-to-skill>/scripts/inspect_pr_checks.py" --repo "." --pr "<number-or-url>"`
     - Add `--json` for machine-friendly output.
3. Scope non-GitHub Actions checks.
   - If the check URL is not a GitHub Actions run, label it as external and only report the URL.
   - Do not attempt Buildkite or other providers; keep the workflow lean.
4. Summarize failures for the user.
   - Provide the failing check name, run URL (if any), and a concise log snippet.
   - Call out missing logs explicitly and do not over-claim certainty.
5. Propose a focused fix plan and wait for approval.
   - Keep the plan tied directly to the failing checks and the observed root cause.
6. Implement after approval.
   - Apply the approved fix locally.
   - Run the most relevant local verification available.
7. Recheck status and summarize residual risk.
   - Rerun the bundled inspection script or the specific failed local check; do not also run `gh pr checks` when the script already returned current PR check state.
   - Report what is still unverified, what may still be flaky, and whether any failing checks were external and therefore not actionable here.

## Output

End with one compact status line:

```text
status=PASS|BLOCKED|PENDING artifacts=<path-or-none> summary=<one line>
```

- `PASS`: GitHub Actions blockers are fixed, or only waived/external non-actionable checks remain.
- `BLOCKED`: the fix needs user approval, missing credentials, missing logs, or a non-GitHub provider.
- `PENDING`: a check rerun was triggered or is still running.

## Bundled Resources

### scripts/inspect_pr_checks.py

Fetch failing PR checks, pull GitHub Actions logs, and extract a failure snippet. Exits non-zero when failures remain so it can be used in automation.

Usage examples:
- `python "<path-to-skill>/scripts/inspect_pr_checks.py" --repo "." --pr "123"`
- `python "<path-to-skill>/scripts/inspect_pr_checks.py" --repo "." --pr "https://github.com/org/repo/pull/123" --json`
- `python "<path-to-skill>/scripts/inspect_pr_checks.py" --repo "." --max-lines 200 --context 40`

## Guardrails

- Treat non-GitHub Actions providers as report-only unless the user explicitly wants a separate investigation path.
- If the failure is clearly unrelated to the local diff, say so before proposing code changes.
