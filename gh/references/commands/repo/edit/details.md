# Details

## Description

Edit repository settings.

To toggle a setting off, use the `--<flag>=false` syntax.

Changing repository visibility can have unexpected consequences including but not limited to:

- Losing stars and watchers, affecting repository ranking
- Detaching public forks from the network
- Disabling push rulesets
- Allowing access to GitHub Actions history and logs

When the `--visibility` flag is used, `--accept-visibility-change-consequences` flag is required.

For information on all the potential consequences, see <https://gh.io/setting-repository-visibility>.

When the `--enable-squash-merge` flag is used, `--squash-merge-commit-message`
can be used to change the default squash merge commit message behavior:

- `default`: uses commit title and message for 1 commit, or pull request title and list of commits for 2 or more
- `pr-title`: uses pull request title
- `pr-title-commits`: uses pull request title and list of commits
- `pr-title-description`: uses pull request title and description

## Arguments

  A repository can be supplied as an argument in any of the following formats:
  - "OWNER/REPO"
  - by URL, e.g. "https://github.com/OWNER/REPO"
