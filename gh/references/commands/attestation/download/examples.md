# Examples

  # Download attestations for a local artifact linked with an organization
  $ gh attestation download example.bin -o github

  # Download attestations for a local artifact linked with a repository
  $ gh attestation download example.bin -R github/example

  # Download attestations for an OCI image linked with an organization
  $ gh attestation download oci://example.com/foo/bar:latest -o github
