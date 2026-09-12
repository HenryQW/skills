# Details

## Description

Pull from remote and do a cascading rebase across the stack.

Ensures that each branch in the stack has the tip of the previous
layer in its commit history, rebasing if necessary.

Use --no-trunk to skip fetching and rebasing with the trunk branch.
Only the inter-branch rebases are performed (branch 2 onto branch 1,
branch 3 onto branch 2, etc.).
