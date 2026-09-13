# gh release edit

Edit a release

**Usage:** `gh release edit <tag>`

## Options
      --discussion-category string   Start a discussion in the specified category when publishing a draft
      --draft                        Save the release as a draft instead of publishing it
      --latest                       Explicitly mark the release as "Latest"
  -n, --notes string                 Release notes
  -F, --notes-file file              Read release notes from file (use "-" to read from standard input)
      --prerelease                   Mark the release as a prerelease
      --tag string                   The name of the tag
      --target branch                Target branch or full commit SHA (default [main branch])
  -t, --title string                 Release title
      --verify-tag                   Abort in case the git tag doesn't already exist in the remote repository
  -R, --repo [HOST/]OWNER/REPO   Select another repository using the [HOST/]OWNER/REPO format

## More
- [Examples](examples.md)
