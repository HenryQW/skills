# Details

## Description

List GitHub rulesets for a repository or organization.

If no options are provided, the current repository's rulesets are listed. You can query a different
repository's rulesets by using the `--repo` flag. You can also use the `--org` flag to list rulesets
configured for the provided organization.

Use the `--parents` flag to control whether rulesets configured at higher levels that also apply to the provided
repository or organization should be returned. The default is `true`.

Your access token must have the `admin:org` scope to use the `--org` flag, which can be granted by running `gh auth refresh -s admin:org`.
