# Details

## Description

Create or update a stack on GitHub from branch names, PR numbers, or PR URLs.

This command does not rely on gh-stack local tracking state. It is
designed for users who manage branches with external tools (e.g. jj,
Sapling, ghstack, git-town, etc...) and want to use GitHub stacked
PRs without adopting local stack tracking.

Arguments are provided in stack order (bottom to top). Each argument
can be a branch name, a PR number, or a PR URL (e.g.
https://github.com/owner/repo/pull/123). For numeric arguments, the
command first checks if a PR with that number exists; if not, it
treats the argument as a branch name. PR URLs are always resolved
as pull requests (never as branch names).

Branch arguments are automatically pushed to the remote before
creating or looking up PRs. For branches that already have open PRs,
those PRs are used. For branches without PRs, new PRs are created
automatically with the correct base branch chaining.

If the PRs are not yet in a stack, a new stack is created. If some of
the PRs are already in a stack, the existing stack is updated to include
the new PRs (existing PRs are never removed).

As a shortcut for growing an existing stack, pass a stack number as the
first argument (the number shown in the GitHub stack UI). The remaining
arguments are appended to the top of that stack, so you don't have to
re-list its current PRs. Arguments already in the stack are skipped;
arguments that belong to a different stack are rejected. Because stack and
PR numbers never overlap, a numeric first argument is treated as a stack
only when it matches an existing stack.
