# Details

## Description

Verify that a given asset file originated from a specific GitHub Release using cryptographically signed attestations.

An attestation is a claim made by GitHub regarding a release and its assets.

		This command checks that the asset you provide matches a valid attestation for the specified release (or the latest release, if no tag is given).
It ensures the asset's integrity by validating that the asset's digest matches the subject in the attestation and that the attestation is associated with the release.

For more information about output formatting flags, see `gh help formatting`.
