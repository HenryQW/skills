# Details

## Description

Initialize a new stack of branches in the current repository.

You can pass multiple branch names to create a multi-layer stack in one
command. Existing branches are adopted automatically; missing branches are
created. By default, the first branch is based on the default branch, and
each subsequent branch is based on the previous one.

Use --base to specify a different trunk branch.
