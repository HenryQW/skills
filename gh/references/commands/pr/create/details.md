# Details

## Description

Create a pull request on GitHub.

Upon success, the URL of the created pull request will be printed.

When the current branch isn't fully pushed to a git remote, a prompt will ask where
to push the branch and offer an option to fork the base repository. Any fork created this
way will only have the default branch of the upstream repository. Use `--head` to
explicitly skip any forking or pushing behavior.

`--head` supports `<user>:<branch>` syntax to select a head repo owned by `<user>`.
Using an organization as the `<user>` is currently not supported.
For more information, see <https://github.com/cli/cli/issues/10093>

A prompt will also ask for the title and the body of the pull request. Use `--title` and
`--body` to skip this, or use `--fill` to autofill these values from git commits.
It's important to notice that if the `--title` and/or `--body` are also provided
alongside `--fill`, the values specified by `--title` and/or `--body` will
take precedence and overwrite any autofilled content.

The base branch for the created PR can be specified using the `--base` flag. If not provided,
the value of `gh-merge-base` git branch config will be used. If not configured, the repository's
default branch will be used. Run `git config branch.{current}.gh-merge-base {base}` to configure
the current branch to use the specified merge base.

Link an issue to the pull request by referencing the issue in the body of the pull
request. If the body text mentions `Fixes #123` or `Closes #123`, the referenced issue
will automatically get closed when the pull request gets merged.

Use `--attach` to upload an image or video. The attachment is appended to the
body. If the body references an attached file, such as `![alt](./login.png)`, that
reference is rewritten to point at the uploaded asset instead.
You can attach up to 50 files per command.

Alt text for an image follows the path after `#`, as in
`--attach './login.png#The login error state'`. Without it the filename is used.
A reference already in the body keeps the alt text written there. Video renders
as a player and has no alt text, so it cannot be given any.

If some attachments upload and others fail, the pull request is still created with the
ones that succeeded. The command then exits with a non-zero status, but the new pull
request's URL is still printed to stdout.

By default, users with write access to the base repository can push new commits to the
head branch of the pull request. Disable this with `--no-maintainer-edit`.

Adding a pull request to projects requires authorization with the `project` scope.
To authorize, run `gh auth refresh -s project`.
