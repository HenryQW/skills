# Options

## Flags

  -b, --bundle string                Path to bundle on disk, either a single bundle in a JSON file or a JSON lines file with multiple bundles
      --bundle-from-oci              When verifying an OCI image, fetch the attestation bundle from the OCI registry instead of from GitHub
      --cert-identity string         Enforce that the certificate's SubjectAlternativeName matches the provided value exactly
  -i, --cert-identity-regex string   Enforce that the certificate's SubjectAlternativeName matches the provided regex
      --cert-oidc-issuer string      Enforce that the issuer of the OIDC token matches the provided value (default "https://token.actions.githubusercontent.com")
      --custom-trusted-root string   Path to a trusted_root.jsonl file; likely for offline verification
      --deny-self-hosted-runners     Fail verification for attestations generated on self-hosted runners
  -d, --digest-alg string            The algorithm used to compute a digest of the artifact: {sha256|sha512} (default "sha256")
      --format string                Output format: {json}
      --hostname string              Configure host to use
  -q, --jq expression                Filter JSON output using a jq expression
  -L, --limit int                    Maximum number of attestations to fetch (default 30)
      --no-public-good               Do not verify attestations signed with Sigstore public good instance
  -o, --owner string                 GitHub organization to scope attestation lookup by
      --predicate-type string        Enforce that verified attestations' predicate type matches the provided value (default "https://slsa.dev/provenance/v1")
  -R, --repo string                  Repository name in the format <owner>/<repo>
      --signer-digest string         Enforce that the digest associated with the signer workflow matches the provided value
      --signer-repo string           Enforce that the workflow that signed the attestation's repository matches the provided value (<owner>/<repo>)
      --signer-workflow string       Enforce that the workflow that signed the attestation matches the provided value ([host/]<owner>/<repo>/<path>/<to>/<workflow>)
      --source-digest string         Enforce that the digest associated with the source repository matches the provided value
      --source-ref string            Enforce that the git ref associated with the source repository matches the provided value
  -t, --template string              Format JSON output using a Go template; see "gh help formatting"

## Inherited Flags

  --help   Show help for command
