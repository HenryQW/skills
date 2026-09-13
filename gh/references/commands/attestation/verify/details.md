# Details

## Description

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
