# Details

## Description

Push active branches in the current stack to the remote.

Uses explicit per-branch --force-with-lease checks. Updates are not atomic: a
branch may update even if another branch is rejected. Fix the rejected branch
and run the command again; branches already updated will be unchanged.
Merged and queued branches are automatically skipped.
