# Details

## Description

Create a new GitHub Release for a repository.

A list of asset files may be given to upload to the new release. To define a
display label for an asset, append text starting with `#` after the file name.

If a matching git tag does not yet exist, one will automatically get created
from the latest state of the default branch.
Use `--target` to point to a different branch or commit for the automatic tag creation.
Use `--verify-tag` to abort the release if the tag doesn't already exist.
To fetch the new tag locally after the release, do `git fetch --tags origin`.

To create a release from an annotated git tag, first create one locally with
git, push the tag to GitHub, then run this command.
Use `--notes-from-tag` to get the release notes from the annotated git tag.
If the tag is not annotated, the commit message will be used instead.

Use `--generate-notes` to automatically generate notes using GitHub Release Notes API.
When using automatically generated release notes, a release title will also be automatically
generated unless a title was explicitly passed. Additional release notes can be prepended to
automatically generated notes by using the `--notes` flag.

By default, the release is created even if there are no new commits since the last release.
This may result in the same or duplicate release which may not be desirable in some cases.
Use `--fail-on-no-commits` to fail if no new commits are available. This flag has no
effect if there are no existing releases or this is the very first release.

## Immutable Releases

When release immutability is enabled for a repository, the following protections are enforced:
- Git tags associated with a release cannot be modified or deleted.
- Release assets cannot be modified or deleted.

Immutability is enforced only after a release is published. Draft releases can be modified
or deleted, and the associated git tags can be modified or deleted as well.

When using the `create` command to attach assets to a release, separate API calls
are made to create the release as a draft, upload the assets, and then publish the release.
Immutability protections will be enforced ONLY after the release is published.
