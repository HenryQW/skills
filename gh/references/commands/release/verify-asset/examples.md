# Examples

  # Verify an asset from the latest release
  $ gh release verify-asset ./dist/my-asset.zip

  # Verify an asset from a specific release tag
  $ gh release verify-asset v1.2.3 ./dist/my-asset.zip

  # Verify an asset from a specific release tag and output the attestation in JSON format
  $ gh release verify-asset v1.2.3 ./dist/my-asset.zip --format json
