# Details

## Description

### NOTE: This feature is currently in public preview, and subject to change.

Download attestations associated with an artifact for offline use.

The command requires either:
* a file path to an artifact, or
* a container image URI (e.g. `oci://<image-uri>`)
  * (note that if you provide an OCI URL, you must already be authenticated with
its container registry)

In addition, the command requires either:
* the `--repo` flag (e.g. --repo github/example).
* the `--owner` flag (e.g. --owner github), or

The `--repo` flag value must match the name of the GitHub repository
that the artifact is linked with.

The `--owner` flag value must match the name of the GitHub organization
that the artifact's linked repository belongs to.

Any associated bundle(s) will be written to a file in the
current directory named after the artifact's digest. For example, if the
digest is "sha256:1234", the file will be named "sha256:1234.jsonl".

Colons are special characters on Windows and cannot be used in
file names. To accommodate, a dash will be used to separate the algorithm
from the digest in the attestations file name. For example, if the digest
is "sha256:1234", the file will be named "sha256-1234.jsonl".
