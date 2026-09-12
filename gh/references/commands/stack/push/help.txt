Push active branches in the current stack to the remote.

Uses explicit per-branch --force-with-lease checks. Updates are not atomic: a
branch may update even if another branch is rejected. Fix the rejected branch
and run the command again; branches already updated will be unchanged.
Merged and queued branches are automatically skipped.

Usage:
  gh stack push [flags]

Examples:
  # Push active stack branches to the default remote
  $ gh stack push

  # Push to a specific remote
  $ gh stack push --remote upstream

Flags:
  -h, --help            help for push
      --remote string   Remote to push to (defaults to auto-detected remote)
