# Examples

  # Interactively create a release
  $ gh release create

  # Interactively create a release from specific tag
  $ gh release create v1.2.3

  # Non-interactively create a release
  $ gh release create v1.2.3 --notes "bugfix release"

  # Use automatically generated via GitHub Release Notes API release notes
  $ gh release create v1.2.3 --generate-notes

  # Use release notes from a file
  $ gh release create v1.2.3 -F release-notes.md

  # Use tag annotation or associated commit message as notes
  $ gh release create v1.2.3 --notes-from-tag

  # Don't mark the release as latest
  $ gh release create v1.2.3 --latest=false

  # Upload all tarballs in a directory as release assets
  $ gh release create v1.2.3 ./dist/*.tgz

  # Upload a release asset with a display label
  $ gh release create v1.2.3 '/path/to/asset.zip#My display label'

  # Create a release and start a discussion
  $ gh release create v1.2.3 --discussion-category "General"

  # Create a release only if there are new commits available since the last release
  $ gh release create v1.2.3 --fail-on-no-commits
