# gh attestation trusted-root

Output contents for a trusted_root.jsonl file, likely for offline verification.

**Usage:** `gh attestation trusted-root [--tuf-url <url> --tuf-root <file-path>] [--verify-only] [flags]`

## Options
  --hostname string   Configure host to use
  --tuf-root string   Path to the TUF root.json file on disk
  --tuf-url string    URL to the TUF repository mirror
  --verify-only       Don't output trusted_root.jsonl contents

## More
- [Examples](examples.md)
- [Details](details.md)
