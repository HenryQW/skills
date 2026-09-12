# Details

## Description

Create a new GitHub repository.

To create a repository interactively, use `gh repo create` with no arguments.

To create a remote repository non-interactively, supply the repository name and one of `--public`, `--private`, or `--internal`.
Pass `--clone` to clone the new repository locally.

If the `OWNER/` portion of the `OWNER/REPO` name argument is omitted, it
defaults to the name of the authenticating user.

To create a remote repository from an existing local repository, specify the source directory with `--source`.
By default, the remote repository name will be the name of the source directory.

Pass `--push` to push any local commits to the new repository. If the repo is bare, this will mirror all refs.

For language or platform .gitignore templates to use with `--gitignore`, <https://github.com/github/gitignore>.

For license keywords to use with `--license`, run `gh repo license list` or visit <https://choosealicense.com>.

The repo is created with the configured repository default branch, see <https://docs.github.com/en/account-and-profile/setting-up-and-managing-your-personal-account-on-github/managing-user-account-settings/managing-the-default-branch-name-for-your-repositories>.
