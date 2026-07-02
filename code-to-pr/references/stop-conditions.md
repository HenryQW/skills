# Stop conditions

Stop instead of guessing when any condition applies:

- The current branch is the base branch.
- Greptile fails to run.
- A Greptile finding is real but needs a product decision.
- A finding asks for optional cleanup, broad refactoring, or behavior outside the issue scope.
- A finding is not observable in `git diff <base_branch>...HEAD`.
- The same actionable finding repeats after a reasonable targeted fix.
- A fix would modify forbidden paths without a deterministic Greptile finding in those files.
- The diff expands beyond review scope.
- Actionable findings remain after the iteration budget.

Do not open a PR until no actionable Greptile findings remain.
