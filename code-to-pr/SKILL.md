---
name: code-to-pr
description: Use this skill when asked to run Greptile review on the current issue branch, apply actionable review fixes, push the branch, and open a GitHub pull request. It returns only the PR URL. Do not use this skill to implement a fresh issue from scratch.
---
# code-to-pr

## Goal

Run Greptile review loops on the current non-base branch, fix actionable findings, push, and open a PR.
Assume implementation work already exists.

## Bundled resources

- `scripts/diff_guard.py`: forbidden-path guard.
- `scripts/greptile_compact.py`: compact Greptile JSON output.
- `scripts/validation_candidates.py`: validation command suggestions.
- `scripts/pr_body.py`: fallback PR body generation.
- `references/greptile-review.md`: actionability and fix rules.
- `references/stop-conditions.md`: stop instead of guessing.

## Inputs

- `base_branch` is required.
- `issue_number` is optional.
- `max_iterations` is optional and defaults to `3`.
- `draft_pr` is optional and defaults to `false`.

## Hard boundaries

- Do not run on the base branch.
- Greptile review output is the only review signal for this skill.
- Fix only actionable Greptile findings.
- Only modify files related to actionable findings.
- Do not expand product scope.
- Do not perform unrelated refactors.
- Do not modify secrets, env files, generated files, lockfiles, `.context/`, `.agents/`, or infrastructure files unless Greptile directly identifies an issue in those files and the fix is deterministic.
- Do not use `git add .` unless the full diff has been inspected.
- Use Conventional Commits.
- Open a PR only when no actionable Greptile findings remain.
- Return only the PR URL on success.

Read `references/greptile-review.md` before classifying findings.
Read `references/stop-conditions.md` whenever a stop condition may apply.

## Procedure

### 1. Confirm branch and working tree

Run:

```bash
git branch --show-current
git status --short
```

Stop if the current branch is base_branch.

If the working tree is dirty, inspect the diff before continuing.

Do not overwrite or discard user changes.

### 2. Establish diff scope

Run:

```bash
git diff <base_branch>...HEAD --stat
git diff <base_branch>...HEAD
python3 <skill_dir>/scripts/diff_guard.py --base <base_branch>
```

Use this diff as the review scope. Fixes must stay inside it unless a directly necessary adjacent file is required.

### 3. Review and fix loop

Repeat up to max_iterations. Default max_iterations is 3.

Run exactly:

```bash
greptile review --json --no-color
```

If the output is too noisy to classify, rerun the same command through the compact helper:

```bash
greptile review --json --no-color | python3 <skill_dir>/scripts/greptile_compact.py
```

If Greptile fails, stop. If no actionable findings remain, exit the loop.

Classify findings with `references/greptile-review.md`. Ignore non-actionable findings.

Apply only the smallest deterministic fixes for actionable findings.

### 4. Inspect and validate each fix

After each fix iteration, run:


```bash
git status --short
git diff --stat
git diff
python3 <skill_dir>/scripts/diff_guard.py --base <base_branch>
python3 <skill_dir>/scripts/validation_candidates.py --base <base_branch>
```

Run the smallest relevant suggested validation command.

Stage explicit inspected paths only:

```bash
git add <file1> <file2>
```

Commit using Conventional Commits. Use `fix` unless another type is clearly more accurate:

```bash
git commit -m "fix(api): handle missing review edge case"
```

Each iteration must resolve at least one actionable finding or reduce the actionable finding set.

### 5. Final review gate

Run Greptile one final time:

```bash
greptile review --json --no-color
```

Open a PR only if no actionable findings remain.

Stop if actionable findings remain after the iteration budget.

### 6. Push

Run:

```bash
git push --set-upstream origin HEAD
```

### 7. Create PR

Inspect whether the repository has a PR template.

Use the PR template if present.

If no PR template exists, draft a body with:

```bash
python3 <skill_dir>/scripts/pr_body.py <base_branch> [--issue-number <issue_number>] [--issue-link closes|refs] [--test <command-or-result>] [--body-file <path>]
```

If issue_number is provided and the implementation fully resolves the issue, include:

```text
Closes #<issue_number>
```

If the branch only partially addresses the issue, include:

```text
Refs #<issue_number>
```

Use a concise title.

Prefer:

```text
Fix #<issue_number>
```

or a short behavior-focused title when more descriptive.

Create the PR with gh pr create.

Use --draft only when draft_pr is true.

### 8. Output

Return only the PR URL.

Do not include explanations.

Do not include summaries.

Do not include markdown.
