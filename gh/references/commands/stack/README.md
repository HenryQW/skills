# gh stack

Stacked PRs let you break a large change into a chain of pull requests that build on each other.

**Usage:** `gh stack [command]`

## Commands
- [`add`](add/) — Add a new branch on top of the current stack
- [`checkout`](checkout/) — Checkout a stack by stack number, PR number, PR URL, or branch name
- [`init`](init/) — Initialize a new stack
- [`modify`](modify/) — Interactively restructure a stack
- [`unstack`](unstack/) — Remove a stack locally and on GitHub
- [`view`](view/) — View the current stack
- [`link`](link/) — Link PRs into a stack on GitHub without local tracking
- [`merge`](merge/) — Merge a stack of pull requests
- [`push`](push/) — Push active branches in the current stack to the remote
- [`rebase`](rebase/) — Rebase a stack of branches
- [`submit`](submit/) — Create a stack of PRs on GitHub
- [`sync`](sync/) — Sync the current stack with the remote
- [`bottom`](bottom/) — Check out the bottom branch of the stack (closest to the trunk)
- [`down`](down/) — Check out a branch further down in the stack (closer to the trunk)
- [`switch`](switch/) — Interactively switch to another branch in the stack
- [`top`](top/) — Check out the top branch of the stack (furthest from the trunk)
- [`trunk`](trunk/) — Check out the trunk branch of the stack
- [`up`](up/) — Check out a branch further up in the stack (further from the trunk)
- [`alias`](alias/) — Create a shell alias for gh stack
- [`feedback`](feedback/) — Submit feedback for gh-stack

## Options
  -v, --version   version for stack


## More
- [Examples](examples.md)
- [Details](details.md)
