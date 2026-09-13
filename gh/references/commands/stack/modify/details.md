# Details

## Description

Open an interactive TUI to restructure the current stack.

Operations available:
  • Drop branches from the stack
  • Fold branches into adjacent branches
  • Insert new branches into the stack
  • Reorder branches
  • Rename branches

All changes are staged in the TUI and applied together when you press Ctrl+S.
If your changes affect branches with pull requests, run 'gh stack submit'
afterward to push changes, update PRs, and recreate the stack on GitHub.
