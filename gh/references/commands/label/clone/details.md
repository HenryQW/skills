# Details

## Description

Clones labels from a source repository to a destination repository on GitHub.
By default, the destination repository is the current repository.

All labels from the source repository will be copied to the destination
repository. Labels in the destination repository that are not in the source
repository will not be deleted or modified.

Labels from the source repository that already exist in the destination
repository will be skipped. You can overwrite existing labels in the
destination repository using the `--force` flag.
