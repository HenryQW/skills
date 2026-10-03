# Entries

<a id="endpoint-get-feed-entry"></a>
## Get Feed Entry

Request:

    GET /v1/feeds/42/entries/888

Response:

[Entry](models.md#entry) object.

<a id="endpoint-get-entry"></a>
## Get Entry

Request:

    GET /v1/entries/888

Response:

[Entry](models.md#entry) object.

<a id="endpoint-import-entry"></a>
## Import Entry

Request:

    POST /v1/feeds/{feedID}/entries/import
    Content-Type: application/json

    {
        "title": "Entry Title",
        "url": "http://example.org/article.html",
        "author": "Foobar",
        "content": "<p>HTML contents</p>",
        "published_at": 1736200000,
        "status": "unread",
        "starred": false,
        "tags": ["tag1", "tag2"],
        "external_id": "unique-id-123",
        "comments_url": "http://example.org/article.html#comments"
    }

All fields are optional except `url`. `title`, `url`, `author`, `content`, `external_id`, and `comments_url` are strings; `published_at` is Unix seconds; `status` is `read` or `unread`; `starred` is boolean; `tags` is an array of strings.

In the pinned implementation, omitted status defaults to **read**, omitted/non-positive publication time defaults to now, and omitted title defaults to the URL. Identity is derived from `external_id` when provided, otherwise URL, within the feed. Importing an existing entry can still assign its status and star it; a `200` is not a guarantee of no side effects. Do not use import as a read-only existence check.

Response:

```json
{
    "id": 1790
}
```

Returns a `201 Created` status code when the entry is created, and a `200 OK` status code when the entry already exists.

This API endpoint is available since Miniflux v2.2.16.

<a id="endpoint-update-entry"></a>
## Update Entry

Both string fields `title` and `content` are optional. Send only intended changes. The pinned validator rejects explicitly empty strings; this endpoint cannot clear either field by sending `""`.

Request:

    PUT /v1/entries/{entryID}

    {
        "title": "New title",
        "content": "Some text"
    }

Response:

[Entry](models.md#entry) object.

Returns a `201 Created` status code for success.

This API endpoint is available since Miniflux v2.0.49.

<a id="endpoint-save-entry"></a>
## Save entry to third-party services

Request:

    POST /v1/entries/{entryID}/save

Response:

Returns a `202 Accepted` status code for success.

<a id="endpoint-fetch-content"></a>
## Fetch original article

Request:

    GET /v1/entries/{entryID}/fetch-content?update_content=false

Available fields:

- `update_content`: true or false. (default false). Whether to replace title and content in database

Response:

```json
{"content": "html content"}
```

This API endpoint is available since Miniflux v2.0.36.

<a id="endpoint-get-category-entries"></a>
## Get Category Entries

Request:

    GET /v1/categories/22/entries?limit=1&order=id&direction=asc

Filters: see [Get Entries](#endpoint-get-entries). For these scoped routes, `category_id` is available since 2.0.19 rather than 2.0.24.

Response:

`{"total": N, "entries": [...]}`; each element is an [Entry](models.md#entry). `total` is the matching count, not the page length.

<a id="endpoint-get-feed-entries"></a>
## Get Feed Entries

Request:

    GET /v1/feeds/42/entries?limit=1&order=id&direction=asc

Filters: see [Get Entries](#endpoint-get-entries). For these scoped routes, `category_id` is available since 2.0.19 rather than 2.0.24.

Response:

`{"total": N, "entries": [...]}`; each element is an [Entry](models.md#entry). `total` is the matching count, not the page length.

<a id="endpoint-get-entries"></a>
## Get Entries

Request:

    GET /v1/entries?status=unread&direction=desc

Available filters:

- `status`: `read` or `unread`; repeat the query key to select multiple statuses (>=2.0.24). The supplied manual also lists `removed`, but the pinned validator rejects it; do not rely on that value without checking the deployed release.
- `offset`
- `limit`
- `order`: "id", "status", "published\_at", "category\_title",
"category\_id"
- `direction`: "asc" or "desc"
- `before` (unix timestamp, available since Miniflux 2.0.9)
- `after` (unix timestamp, available since Miniflux 2.0.9)
- `published_before` (unix timestamp, available since Miniflux 2.0.49)
- `published_after` (unix timestamp, available since Miniflux 2.0.49)
- `changed_before` (unix timestamp, available since Miniflux 2.0.49)
- `changed_after` (unix timestamp, available since Miniflux 2.0.49)
- `before_entry_id` (int64, available since Miniflux 2.0.9)
- `after_entry_id` (int64, available since Miniflux 2.0.9)
- `starred` (boolean, available since Miniflux 2.0.9)
- `search`: search query (text, available since Miniflux 2.0.10)
- `category_id`: filter by category (int, available since Miniflux 2.0.24)
- `globally_visible`: filter on globally visible entries (boolean, available since Miniflux 2.2.0)

Response:

`{"total": N, "entries": [...]}`; each element is an [Entry](models.md#entry). `total` is the matching count, not the page length.

<a id="endpoint-get-entry-ids"></a>
## Get Entry IDs

Return a list of ID values for entries meeting the specified criteria. Results are limited to 10,000 ID values per response by default.

Request:

    GET /v1/entries/ids?status=unread

Available filters:

- `status`: Entry status (read or unread)
- `starred`: true or false
- `offset`
- `limit`: Maximum 10,000

Response

```json
{
    "total": 2,
    "entry_ids": [
        15548,
        15540
    ]
}
```

This API endpoint is available since Miniflux v2.3.2.

<a id="endpoint-update-entries"></a>
## Update Entries

Request:

    PUT /v1/entries
    Content-Type: application/json

    {
        "entry_ids": [1234, 4567],
        "status": "read",
        "starred": true
    }

Send a non-empty integer `entry_ids` array and either `status` (`read` or `unread`), `starred` (boolean), or both. Omit the property you do not intend to change; `starred: false` explicitly unstars. Returns `204` with no body. These are explicit assignments, not toggles.

The ability to send "starred" is available since Miniflux v2.3.2.

<a id="endpoint-toggle-bookmark"></a>
## Toggle Entry Bookmark

Request:

    PUT /v1/entries/1234/bookmark

Returns `204` with no body. This **toggles** starred state; it does not mean "set starred to true". Do not retry blindly after a timeout. Prefer bulk `starred` assignment on >=2.3.2.

<a id="endpoint-get-enclosure"></a>
## Get Enclosure

Request:

    GET /v1/enclosures/{enclosureID}

Response:

```json
{
  "id": 278,
  "user_id": 1,
  "entry_id": 195,
  "url": "https://example.org/file",
  "mime_type": "application/octet-stream",
  "size": 0,
  "media_progression": 0
}
```

This API endpoint has been available since Miniflux v2.2.0.

<a id="endpoint-update-enclosure"></a>
## Update Enclosure

Request:

    PUT /v1/enclosures/{enclosureID}

    {
        "media_progression": 42
    }

Returns a `204` status code for success.

This API endpoint has been available since Miniflux v2.2.0.

<a id="integrations-status"></a>
## Integrations Status

This API endpoint returns `true` if the authenticated user has enabled an integration to save entries to a third-party service (e.g., Wallabag, Shiori, Shaarli). Note that the Google Reader API and Fever API are not considered.

Request:

    GET /v1/integrations/status

Response:

    {"has_integrations": true}

This API endpoint is available since Miniflux v2.2.2.

## Source-verified listing semantics and extra routes

The pinned handler/validator additionally supports the following; minimum versions are not documented in the supplied manual:

- `feed_id` (integer): restrict the global list to a feed. Prefer the scoped feed route when no cross-scope filtering is needed.
- Repeated `tags` (strings): case-insensitive matching requiring all requested tags.
- Additional `order` values: `changed_at`, `created_at`, `title`, `author`.
- Default listing `limit` is 100; `offset` is zero. Set order/direction/limit explicitly for reproducible collection.
- `before` and `after` refer to publication time, like `published_before` and `published_after`. All time filters use Unix seconds and strict `<`/`>` comparisons; entry-ID filters are also strict.
- `globally_visible=true` restricts to globally visible feeds/categories. False or omitted does **not** mean hidden-only; it imposes no visibility restriction in this implementation.
- Do not combine scoped paths with contradictory `feed_id`/`category_id` queries: the handler can replace path scope with query scope.
- `GET /v1/categories/{categoryID}/entries/{entryID}` returns an [Entry](models.md#entry) constrained to that category, like the feed-scoped single-entry route.
- `PUT /v1/entries/{entryID}/star` is an alias of `/bookmark`, also a toggle (204), not an explicit assignment.
- `fetch-content` additionally returns `reading_time` in the pinned implementation. Continue to use its `content` field rather than treating it as an Entry.
- `/v1/entries/ids` sorts IDs descending and permits only its listed filters; it has no keyset, category, feed, search, or time filters.
