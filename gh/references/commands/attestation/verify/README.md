Verify the integrity and provenance of an artifact using its associated
cryptographically signed attestations.

## Understanding Verification

An attestation is a claim (i.e. a provenance statement) made by an actor
(i.e. a GitHub Actions workflow) regarding a subject (i.e. an artifact).

In order to verify an attestation, you must provide an artifact and validate:
* the identity of the actor that produced the attestation
* the expected attestation predicate type (the nature of the claim)

By default, this command enforces the `https://slsa.dev/provenance/v1`
predicate type. To verify other attestation predicate types use the
`--predicate-type` flag.

The "actor identity" consists of:
* the repository or the repository owner the artifact is linked with
* the Actions workflow that produced the attestation (a.k.a the
  signer workflow)

This identity is then validated against the attestation's certificate's
SourceRepository, SourceRepositoryOwner, and SubjectAlternativeName
(SAN) fields, among others.

It is up to you to decide how precisely you want to enforce this identity.

At a minimum, this command requires either:
* the `--owner` flag (e.g. --owner github), or
* the `--repo` flag (e.g. --repo github/example)

The more precisely you specify the identity, the more control you will
have over the security guarantees offered by the verification process.

Ideally, the path of the signer workflow is also validated using the
`--signer-workflow` or `--cert-identity` flags.

Please note: if your attestation was generated via a reusable workflow then
that reusable workflow is the signer whose identity needs to be validated.
In this situation, you must use either the `--signer-workflow` or
the `--signer-repo` flag.

For more options, see the other available flags.

## Loading Artifacts And Attestations

To specify the artifact, this command requires:
* a file path to an artifact, or
* a container image URI (e.g. `oci://<image-uri>`)
  * (note that if you provide an OCI URL, you must already be authenticated with
its container registry)

By default, this command will attempt to fetch relevant attestations via the
GitHub API using the values provided to `--owner` or  `--repo`.

To instead fetch attestations from your artifact's OCI registry, use the
`--bundle-from-oci` flag.

For offline verification using attestations stored on disk (c.f. the download command)
provide a path to the `--bundle` flag.

## Additional Policy Enforcement

Given the `--format=json` flag, upon successful verification this
command will output a JSON array containing one entry per verified attestation.

This output can then be used for additional policy enforcement, i.e. by being
piped into a policy engine.

Each object in the array contains two properties:
* an `attestation` object, which contains the bundle that was verified
* a `verificationResult` object, which is a parsed representation of the
  contents of the bundle that was verified.

Within the `verificationResult` object you will find:
* `signature.certificate`, which is a parsed representation of the X.509
  certificate embedded in the attestation,
* `verifiedTimestamps`, an array of objects denoting when the attestation
  was witnessed by a transparency log or a timestamp authority
* `statement`, which contains the `subject` array referencing artifacts,
  the `predicateType` field, and the `predicate` object which contains
  additional, often user-controllable, metadata

IMPORTANT: please note that only the `signature.certificate` and the
`verifiedTimestamps` properties contain values that cannot be
manipulated by the workflow that originated the attestation.

When dealing with attestations created within GitHub Actions, the contents of
`signature.certificate` are populated directly from the OpenID Connect
token that GitHub has generated. The contents of the `verifiedTimestamps`
array are populated from the signed timestamps originating from either a
transparency log or a timestamp authority – and likewise cannot be forged by users.

When designing policy enforcement using this output, special care must be taken
when examining the contents of the `statement.predicate` property:
should an attacker gain access to your workflow's execution context, they
could then falsify the contents of the `statement.predicate`.

To mitigate this attack vector, consider using a "trusted builder": when generating
an artifact, have the build and attestation signing occur within a reusable workflow
whose execution cannot be influenced by input provided through the caller workflow.

See above re: `--signer-workflow`.

For more information about output formatting flags, see `gh help formatting`.

USAGE
  gh attestation verify [<file-path> | oci://<image-uri>] [--owner | --repo] [flags]

FLAGS
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

INHERITED FLAGS
  --help   Show help for command

EXAMPLES
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

LEARN MORE
  Use `gh <command> <subcommand> --help` for more information about a command.
  Read the manual at https://cli.github.com/manual
  Learn about exit codes using `gh help exit-codes`
  Learn about accessibility experiences using `gh help accessibility`
