---
name: code-to-pr
description: Use this skill when asked to run Greptile review on the current issue branch, apply actionable review fixes, push the branch, and open a GitHub pull request. It returns only the PR URL. Do not use this skill to implement a fresh issue from scratch.
---
# code-to-pr

## Goal

Run Greptile review loops on the current branch, fix actionable findings, push the branch, and open a PR.
This skill assumes implementation work already exists on a non-base branch.

## Bundled resources

- Read `references/greptile-review.md` when classifying findings or deciding whether to stop.
- Use `scripts/pr_body.py` to draft a concise PR body when no repository PR template exists.

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

## Actionability rule

A Greptile finding is actionable only when all conditions are true:

- The finding refers to code visible in the current branch diff.
- The fix is deterministic.
- The fix does not require a product decision.
- The fix can be made without expanding issue scope.
- The fix can be made in the referenced file or a directly necessary adjacent file.

A finding is non-actionable when any condition is true:

- It asks for product clarification.
- It suggests optional cleanup.
- It is not observable in the current diff.
- It requires broad refactoring.
- It conflicts with the issue requirements.
- It repeats after a reasonable fix was already applied.

Ignore non-actionable findings.

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
```

Use this diff as the implementation scope.

Review fixes must remain inside this scope unless a directly necessary adjacent file is required.

### 3. Review and fix loop

Repeat up to max_iterations.

Default max_iterations is 3.

### 3.1 Run Greptile

Run exactly:

```bash
greptile review --json --no-color
```

If Greptile fails, stop.

If Greptile output is empty and the command succeeded, treat it as no actionable findings.

### 3.2 Classify findings

For each finding, classify it as actionable or non-actionable using the actionability rule.

Read `references/greptile-review.md` when a finding is borderline.

Do not fix non-actionable findings.

Do not make speculative improvements.

### 3.3 Exit loop when clean

If there are no actionable findings, exit the loop.

### 3.4 Apply fixes

Apply only the smallest deterministic fixes for actionable findings.

Prefer local edits in referenced files.

Do not introduce new abstractions unless necessary to fix the finding.

Do not add new dependencies unless the finding cannot be fixed otherwise and the dependency is already used elsewhere in the repository.

### 3.5 Inspect the fix diff

Run:

```bash
git status --short
git diff --stat
git diff
```

Check:

- Only intended files changed.
- Every changed file maps to an actionable finding.
- No unrelated refactors or formatting changes were introduced.
- No forbidden files were changed.

Stop if the diff expanded beyond review scope.

### 3.6 Run relevant validation

Run targeted validation commands when discoverable from the repository.

Prefer tests or checks related to changed files.

Do not run destructive commands.

### 3.7 Commit fixes

Stage only inspected files.

Use explicit file paths.

Example:

```bash
git add <file1> <file2>
```

Commit using Conventional Commits.

Use fix for review fixes unless another type is clearly more accurate.

Example:

```bash
git commit -m "fix(api): handle missing review edge case"
```

### 3.8 Progress rule

Each iteration must resolve at least one actionable finding or reduce the actionable finding set.

If the same actionable finding repeats after a fix attempt, stop rather than cycling.

### 4. Final review gate

After the loop, run Greptile one final time:

```bash
greptile review --json --no-color
```

Classify findings again.

Open a PR only if no actionable findings remain.

Stop if actionable findings remain after the iteration budget.

### 5. Push

Run:

```bash
git push --set-upstream origin HEAD
```

### 6. Create PR

Inspect whether the repository has a PR template.

Use the PR template if present.

If no PR template exists, create a concise PR body with these sections:

```markdown
## Summary
- <2 to 4 bullets describing the intentional changes>

## Testing
- <commands run>
- <or "Not run">

## Scope
- <notable exclusions or constraints>
```

You may draft this body with:

```bash
python3 <skill_dir>/scripts/pr_body.py <base_branch> [--issue-number <issue_number>] [--issue-link closes|refs] [--test <command-or-result>]
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

### 7. Output

Return only the PR URL.

Do not include explanations.

Do not include summaries.

Do not include markdown.
