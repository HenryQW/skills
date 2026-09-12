# Details

## Description

Remove a stack from local tracking and unstack it on GitHub.

With no argument, the active stack (the one containing the currently checked out
branch) is unstacked on GitHub and removed from local tracking.

Provide a stack number (the identifier shown in the GitHub stack UI) to
unstack a specific stack on GitHub. This works from anywhere in the repository,
whether or not the stack is checked out locally — the number is unstacked
directly through the GitHub API. If the stack is also available locally, its
local tracking is removed as well.

Use --local to only remove local tracking without touching remote (GitHub).

GitHub decides which pull requests can be unstacked: PRs that are queued for
merge or have auto-merge enabled are left stacked. When some pull requests
remain stacked, the stack is kept (and local tracking, if any, is unchanged).
