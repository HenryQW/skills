# gh attestation download

### NOTE: This feature is currently in public preview, and subject to change.

**Usage:** `gh attestation download [<file-path> | oci://<image-uri>] [--owner | --repo] [flags]`

## Options
  -d, --digest-alg string       The algorithm used to compute a digest of the artifact: {sha256|sha512} (default "sha256")
      --hostname string         Configure host to use
  -L, --limit int               Maximum number of attestations to fetch (default 30)
  -o, --owner string            GitHub organization to scope attestation lookup by
      --predicate-type string   Filter attestations by provided predicate type
  -R, --repo string             Repository name in the format <owner>/<repo>

## More
- [Examples](examples.md)
- [Details](details.md)
