# Greptile review guide

Use this reference when classifying Greptile findings and preparing the PR.

## Scope source

- Treat `git diff <base_branch>...HEAD` as the implementation scope.
- Treat Greptile review sessions as the only review signal for this skill.
- `greptile review --json --no-color` starts a long-running review session and returns a review ID.
- Use `greptile review show <review_id>` to retrieve, poll, or resume that review session.
- Do not start a new review session just to re-read or compact an existing review.
- Use `scripts/greptile_compact.py` when retrieved review output is too noisy.
- Fixes should stay inside files already visible in the branch diff unless a directly necessary adjacent file is required.
- Do not use issue text to expand scope during this skill. Issue text only helps decide whether the branch fully resolves the issue for `Closes` vs `Refs`.

## Actionable findings

A finding is actionable only when all are true:

- It refers to code visible in the current branch diff.
- The fix is deterministic.
- The fix does not require a product decision.
- The fix does not expand issue scope.
- The fix can be made in the referenced file or a directly necessary adjacent file.

Ignore findings that request clarification, broad cleanup, optional improvements, or behavior beyond the issue.

Stop instead of guessing when Greptile identifies a real risk but the correct behavior is a product decision.

## Repeat findings

- If a finding repeats after a reasonable targeted fix, stop instead of cycling.
- If a finding becomes non-actionable after inspection, leave it unfixed and continue only if no actionable findings remain.
- Each committed fix iteration must reduce the actionable finding set.
- After committing review fixes, start a new review session and classify that new review.
- Reuse the latest completed review ID as the final gate only when no commit happened after it.

## Fix discipline

- Make the smallest deterministic edit.
- Prefer local edits in referenced files.
- Do not introduce new abstractions unless required to fix the finding.
- Do not add dependencies unless the dependency is already used elsewhere and no smaller local fix exists.
- Do not touch secrets, env files, generated files, lockfiles, `.context/`, `.agents/`, or infrastructure files unless Greptile directly identifies a deterministic issue in that file.
- Run `scripts/diff_guard.py --base <base_branch>` before staging.

## PR preparation

After the final clean Greptile gate:

- Push with `git push --set-upstream origin HEAD`.
- Use an existing PR template when present.
- If no template exists, use `scripts/pr_body.py` to create a concise body.
- Use `Closes #<issue_number>` only when the branch fully resolves the issue.
- Use `Refs #<issue_number>` when the branch is partial or preparatory.
