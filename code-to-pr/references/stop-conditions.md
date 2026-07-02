# Stop conditions

Stop instead of guessing when any condition applies:

- The current branch is the base branch.
- Greptile fails to run.
- Greptile does not return a review ID.
- A Greptile finding is real but needs a product decision.
- The same actionable finding repeats after a reasonable targeted fix.
- A fix would modify forbidden paths without a deterministic Greptile finding in those files.
- The diff expands beyond review scope.
- Actionable findings remain after the iteration budget.

Ignore non-actionable findings instead of stopping.

Do not open a PR until no actionable Greptile findings remain.
