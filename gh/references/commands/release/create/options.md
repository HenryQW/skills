# Options

## Flags

      --discussion-category string   Start a discussion in the specified category
  -d, --draft                        Save the release as a draft instead of publishing it
      --fail-on-no-commits           Fail if there are no commits since the last release (no impact on the first release)
      --generate-notes               Automatically generate title and notes for the release via GitHub Release Notes API
      --latest                       Mark this release as "Latest" (default [automatic based on date and version]). --latest=false to explicitly NOT set as latest
  -n, --notes string                 Release notes
  -F, --notes-file file              Read release notes from file (use "-" to read from standard input)
      --notes-from-tag               Fetch notes from the tag annotation or message of commit associated with tag
      --notes-start-tag string       Tag to use as the starting point for generating release notes
  -p, --prerelease                   Mark the release as a prerelease
      --target branch                Target branch or full commit SHA (default [main branch])
  -t, --title string                 Release title
      --verify-tag                   Abort in case the git tag doesn't already exist in the remote repository

## Inherited Flags

      --help                     Show help for command
  -R, --repo [HOST/]OWNER/REPO   Select another repository using the [HOST/]OWNER/REPO format
