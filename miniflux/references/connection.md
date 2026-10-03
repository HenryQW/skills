# Connection and clients

## Authority

These references cover every section of the supplied Miniflux API manual (`https://miniflux.app/docs/api.html`), with duplicate response examples consolidated into [Models](models.md). They describe the native REST API, not Fever or Google Reader emulation.

Route corrections and supplemental fields/semantics were verified against upstream revision [`c52bdef6e9811f7c20cebc034a6c0ec6799dc6df`](https://github.com/miniflux/v2/tree/c52bdef6e9811f7c20cebc034a6c0ec6799dc6df): `internal/api/api.go`, `entry_handlers.go`, `internal/model/{feed,entry,user,category}.go`, `internal/validator/entry.go`, and `internal/storage/entry_query_builder.go`. Source-verified extensions without a documented minimum version are not guaranteed on older deployments; check the deployed release before relying on them. For a conflicting contract, use that release's official API documentation/source, not an assumed fallback path.

Corrections to the supplied manual:

- Entry import is `/v1/feeds/{feedID}/entries/import`, not `/feeds/...`.
- Integration status is `/v1/integrations/status`, not `/integrations/status`.
- The pinned entry validator accepts `read` and `unread`, not the manual's `removed` filter value. User-update identity-provider fields also differ; see the resource notes.
- The create-feed response example's trailing comma was removed; generate valid JSON rather than copying documentation syntax errors.

All `/v1` paths are appended to the configured instance base URL (including its base path). Send `Content-Type: application/json` for JSON bodies and `Content-Type: application/xml` for OPML import. Health probe base-path exceptions are in [System](system.md). Resources are scoped to the authenticated account except administrator-only user management; administrator credentials do not turn ordinary entry/feed requests into cross-user queries.

<a id="authentication"></a>
## Authentication

The API supports two authentication mechanisms:

- HTTP Basic authentication with the account username/password.
- Per-application API keys (since version 2.0.21) -> **preferred method**.

To generate a new API token, go to "Settings > API Keys > Create a new API key".

The helper sets `X-Auth-Token` for a configured API key or `Authorization: Basic ...` for configured username/password. Credentials are never accepted as command-line flags, prompted interactively, or embedded in the instance URL.

### Required configuration

Use exactly one source:

1. Explicit `--config FILE` takes priority over `MINIFLUX_CONFIG`.
2. If a config file is selected, it is the entire configuration. Missing/unreadable/invalid files fail; environment credentials are not merged or used as a fallback.
3. Otherwise require `MINIFLUX_URL` plus exactly one authentication mechanism: `MINIFLUX_API_KEY`, or both `MINIFLUX_USERNAME` and `MINIFLUX_PASSWORD`.

Config schema (illustrative values only):

```json
{
  "url": "https://miniflux.example.org/reader",
  "api_key": "YOUR_APPLICATION_KEY"
}
```

For Basic authentication, replace `api_key` with `username` and `password`. Unknown fields, empty values, incomplete Basic credentials, or simultaneous key/Basic auth fail before network access. Set file permissions to `0600` and keep config/response files outside version control; do not place real secrets in shell arguments, transcripts, or examples.

The URL is the instance base, including any deployment path but excluding `/v1`. HTTPS is mandatory unless `--allow-http` explicitly permits trusted plaintext HTTP. URLs with embedded credentials, query strings, fragments, or a `/v1` suffix are rejected. Redirects are never followed. The default request timeout is 30 seconds; `--timeout SECONDS` must be positive.

### Deterministic commands

Resolve `MF` to the absolute `scripts/miniflux.py` path within this skill. Global flags (`--config`, `--allow-http`, `--timeout`) precede `check` / `request`.

Authenticate first; output is only status and minimal user identity:

```bash
python3 "$MF" check
# Alternatively, select the complete JSON config:
python3 "$MF" --config "$MINIFLUX_CONFIG" check
```

Read requests and repeated URL-encoded query fields:

```bash
python3 "$MF" request GET /v1/feeds
python3 "$MF" request GET /v1/version
python3 "$MF" request GET /v1/entries \
  --query status=read --query status=unread --query starred=false \
  --query limit=100 --query order=id --query direction=asc
python3 "$MF" request GET /v1/entries/888/fetch-content \
  --query update_content=false
```

Mutations require the caller's authorization and `--allow-write`. JSON input is validated, then sent unchanged; `--json -` reads stdin. For example, **only if those exact IDs were authorized**:

```bash
printf '%s' '{"entry_ids":[1234,4567],"status":"read"}' | \
  python3 "$MF" request PUT /v1/entries --allow-write --json -
python3 "$MF" request POST /v1/import --allow-write --body subscriptions.opml
```

`--body FILE` sends raw OPML with `application/xml`; `--body -` reads XML stdin. `--json` and `--body` are mutually exclusive. GET cannot carry a body. `fetch-content` with an `update_content` value other than explicit `false` also requires the write flag.

Terminal JSON wraps the response as `{status, data}`. Sensitive credential fields and matching secret strings are redacted. Empty successes (e.g. 204) return only `{status}`. Non-JSON responses return status/type/byte count; use private file output for exact OPML, probe text, or credential-bearing responses:

```bash
python3 "$MF" request GET /v1/export --output "$PRIVATE_OUTPUT/subscriptions.opml"
python3 "$MF" request GET /v1/api-keys --output "$PRIVATE_OUTPUT/api-keys.json"
```

The destination must be **new**; it is reserved with mode `0600` before sending, so an existing/unwritable output path cannot trigger a mutation. Raw response files can contain credentials: never display, commit, or publish them. Failure may leave an empty/incomplete file; trust it only after exit 0. Terminal output after saving reports status and byte count, not raw data.

All documented `/v1/...` routes use the configured base path. `/healthcheck` and legacy `/version` also use it; liveness/readiness aliases target the instance origin root. Only native API/probe/version paths are accepted, not arbitrary article URLs. The helper performs one attempt and returns exit 1 on config, auth, HTTP, network, or I/O failure.

<a id="clients"></a>
## Clients

Official [Go](https://pkg.go.dev/miniflux.app/v2/client) and [Python](https://github.com/miniflux/python-client) clients exist for application code. Agent-run operations use the bundled helper.

<a id="status-codes"></a>
## Status Codes

- `200`: Everything is OK
- `201`: Resource created/modified
- `204`: Resource removed/modified
- `400`: Bad request
- `401`: Unauthorized (bad username/password)
- `403`: Forbidden (access not allowed)
- `404`: Resource absent (explicitly documented for missing feed icons; inspect the actual response for other resources).
- `500`: Internal server error

Endpoint-specific successes also include `202` (accepted/queued) and `204` (no response body). A proxy may return non-JSON errors or rate-limit responses.

<a id="error-response"></a>
## Error Response

``` json
{
    "error_message": "Some error"
}
```

