# Examples

  # Interactively select a run to view, optionally selecting a single job
  $ gh run view

  # View a specific run
  $ gh run view 12345

  # View a specific run with specific attempt number
  $ gh run view 12345 --attempt 3

  # View a specific job within a run
  $ gh run view --job 456789

  # View the full log for a specific job
  $ gh run view --log --job 456789

  # Exit non-zero if a run failed
  $ gh run view 0451 --exit-status && echo "run pending or passed"
