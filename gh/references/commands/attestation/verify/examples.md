# Examples

  # Verify an artifact linked with a repository
  $ gh attestation verify example.bin --repo github/example

  # Verify an artifact linked with an organization
  $ gh attestation verify example.bin --owner github

  # Verify an artifact and output the full verification result
  $ gh attestation verify example.bin --owner github --format json

  # Verify an OCI image using attestations stored on disk
  $ gh attestation verify oci://<image-uri> --owner github --bundle sha256:foo.jsonl

  # Verify an artifact signed with a reusable workflow
  $ gh attestation verify example.bin --owner github --signer-repo actions/example
