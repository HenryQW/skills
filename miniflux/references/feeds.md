# Feeds

<a id="endpoint-discover"></a>
## Discover Subscriptions

Request:

    POST /v1/discover
    Content-Type: application/json

    {
        "url": "http://example.org"
    }

Response:

```json
[
    {
        "url": "http://example.org/feed.atom",
        "title": "Atom Feed",
        "type": "atom"
    },
    {
        "url": "http://example.org/feed.rss",
        "title": "RSS Feed",
        "type": "rss"
    }
]
```

Optional fields:

- `username`: Feed username (string)
- `password`: Feed password (string)
- `user_agent`: Custom user agent (string)
- `fetch_via_proxy` (boolean)

<a id="endpoint-get-feeds"></a>
## Get Feeds

Request:

    GET /v1/feeds

Response:

Array of [Feed](models.md#feed) objects.

Notes:

- `icon` is `null` when the feed doesn't have any favicon.

<a id="endpoint-get-feed"></a>
## Get Feed

Request:

    GET /v1/feeds/42

Response:

[Feed](models.md#feed) object.

Notes:

- `icon` is `null` when the feed doesn't have any favicon.

<a id="endpoint-get-feed-icon-by-feed-id"></a>
## Get Feed Icon By Feed ID

Request:

    GET /v1/feeds/{feedID}/icon

Response:

```json
{
    "id": 262,
    "data": "image/png;base64,iVBORw0KGgoAAA....",
    "mime_type": "image/png"
}
```

If the feed doesn't have any favicon, a 404 is returned.

<a id="endpoint-get-feed-icon-by-icon-id"></a>
## Get Feed Icon By Icon ID

Request:

    GET /v1/icons/{iconID}

Response:

```json
{
    "id": 262,
    "data": "image/png;base64,iVBORw0KGgoAAA....",
    "mime_type": "image/png"
}
```

This API endpoint is available since Miniflux v2.0.49.

<a id="endpoint-create-feed"></a>
## Create Feed

Request:

    POST /v1/feeds
    Content-Type: application/json

    {
        "feed_url": "http://example.org/feed.atom",
        "category_id": 22
    }

Response:

```json
{
    "feed_id": 262
}
```

Required fields:

- `feed_url`: Feed URL (string)
- `category_id`: Category ID (int, optional since Miniflux >= 2.0.49)

Optional fields:

- `username`: Feed username (string)
- `password`: Feed password (string)
- `crawler`: Enable/Disable scraper (boolean)
- `user_agent`: Custom user agent for the feed (string)
- `scraper_rules`: List of scraper rules (string) - Miniflux >= 2.0.19
- `rewrite_rules`: List of rewrite rules (string) - Miniflux >= 2.0.19
- `blocklist_rules` (string) - Miniflux >= 2.0.27
- `keeplist_rules` (string) - Miniflux >= 2.0.27
- `disabled` (boolean) - Miniflux >= 2.0.27
- `ignore_http_cache` (boolean) - Miniflux >= 2.0.27
- `fetch_via_proxy` (boolean) - Miniflux >= 2.0.27

<a id="endpoint-update-feed"></a>
## Update Feed

Request:

    PUT /v1/feeds/42
    Content-Type: application/json

    {
        "title": "New Feed Title",
        "category_id": 22
    }

Response:

Updated [Feed](models.md#feed) object.

Available fields:

- `feed_url` (string)
- `site_url` (string)
- `title` (string)
- `category_id` (int)
- `scraper_rules` (string)
- `rewrite_rules` (string)
- `blocklist_rules` (string)
- `keeplist_rules` (string)
- `crawler` (boolean)
- `user_agent`: Custom user agent for the feed (string)
- `username` (string)
- `password` (string)
- `disabled` (boolean)
- `ignore_http_cache` (boolean)
- `fetch_via_proxy` (boolean)

<a id="endpoint-refresh-feed"></a>
## Refresh Feed

Request:

    PUT /v1/feeds/42/refresh

    - Returns `204` status code for success.
    - This API call is synchronous and can takes hundred of milliseconds.

<a id="endpoint-refresh-all-feeds"></a>
## Refresh all Feeds

Request:

    PUT /v1/feeds/refresh

    - Returns `204` status code for success.
    - Feeds are refreshed in a background process.
    - Available since Miniflux 2.0.21

<a id="endpoint-remove-feed"></a>
## Remove Feed

Request:

    DELETE /v1/feeds/42

<a id="endpoint-counters"></a>
## Fetch Read/Unread Counters

Request:

    GET /v1/feeds/counters

Response Example:

``` json
{
  "reads": {
    "1": 12,
    "3": 1,
    "4": 1
  },
  "unreads": {
    "1": 7,
    "3": 99,
    "4": 14
  }
}
```

This endpoint is available since Miniflux 2.0.37.

<a id="endpoint-mark-feed-entries-as-read"></a>
## Mark Feed Entries as Read

Request:

    PUT /v1/feeds/123/mark-all-as-read

Returns `204 No Content` status code for success.

This API endpoint is available since Miniflux v2.0.26.

## Source-verified create fields

Additional fields accepted by the pinned FeedCreationRequest for Create Feed; minimum versions are not documented in the supplied manual. Response fields are not automatically writable.

- string: `cookie`, `block_filter_entry_rules`, `keep_filter_entry_rules`, `urlrewrite_rules`, `proxy_url`.
- bool: `ignore_entry_updates`, `no_media_player`, `allow_self_signed_certificates`, `hide_globally`, `disable_http2`.

## Source-verified update fields

The pinned `FeedModificationRequest` also accepts all fields listed in Source-verified create fields above, plus the string `description`. Minimum versions are not documented in the supplied manual. Omitted update fields are unchanged; these are optional updates, not full replacements. Response fields are not automatically writable.
