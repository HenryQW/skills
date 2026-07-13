---
name: "ci-repairbay"
description: "Use when a user asks to inspect, diagnose, or fix failing GitHub PR checks that run in GitHub Actions. Inspection requests stay read-only; explicit fix requests authorize scoped local changes and validation."
---

# CI Repairbay

Use `gh` and the bundled inspector for failing GitHub Actions PR checks.
Inspection, diagnosis, explanation, and review are read-only. An explicit fix
request authorizes only the smallest local fix and relevant non-destructive
validation. External writes, destructive actions, and material scope expansion
still require authorization.

## Memory

Direct invocation calls `$agent-memory load` before resolving the PR and
`$agent-memory distill` immediately before the terminal status. A caller such
as Shipyard owns both instead and retains `.context/decisions.jsonl`. Capture
only confirmed reusable CI root causes, repository guardrails, or durable fix
decisions—not status, logs, run IDs, or transient failures. Memory failure does
not change repair status.

## Inputs

- `repo_path`: target repository, default `.`; pass as `--repo`.
- `pr`: optional number or URL; default current-branch PR.

## Workflow

1. Resolve the URL or PR in `repo_path`; fetch its metadata and changed files.
2. Run:

   ```bash
   python "<skill>/scripts/inspect_pr_checks.py" --repo "." --pr "<number-or-url>"
   ```

   Add `--json`; add `--log-tail` only when the failure snippet is insufficient.
   The script uses native `gh pr checks` and `gh run view --log-failed` output.
3. Report each failing check, run URL, concise evidence, and missing logs without
   overstating certainty. Non-GitHub Actions URLs are external and report-only.
   Inspection or diagnosis stops here.
4. For an explicit fix, inspect the root cause, apply the smallest traceable
   local change, and run the focused repository check. If failure is unrelated
   to the diff, ask before expanding scope.
5. Re-run the inspector or failed local check, not duplicate `gh pr checks`, and
   report remaining external, flaky, pending, or unverified risk.

Finish with:

```text
status=PASS|BLOCKED|PENDING artifacts=<path-or-none> summary=<one line>
```

`PASS` means the requested diagnosis is complete, blockers are fixed, or only
waived/external checks remain. `BLOCKED` means a fix needs authorization,
credentials, logs, or another provider. `PENDING` means a rerun is still active.
