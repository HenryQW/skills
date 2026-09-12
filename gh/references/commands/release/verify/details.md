# Details

## Description

Verify that a GitHub Release is accompanied by a valid cryptographically signed attestation.

An attestation is a claim made by GitHub regarding a release and its assets.

This command checks that the specified release (or the latest release, if no tag is given) has a valid attestation.
It fetches the attestation for the release and prints metadata about all assets referenced in the attestation, including their digests.

For more information about output formatting flags, see `gh help formatting`.
