# Details

## Description

Create a fork of a repository.

With no argument, creates a fork of the current repository. Otherwise, forks
the specified repository.

By default, the new fork is set to be your `origin` remote and any existing
origin remote is renamed to `upstream`. To alter this behavior, you can set
a name for the new fork's remote with `--remote-name`.

The `upstream` remote will be set as the default remote repository.

Additional `git clone` flags can be passed after `--`.
