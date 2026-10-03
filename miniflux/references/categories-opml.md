# Categories and OPML

<a id="endpoint-get-category-feeds"></a>
## Get Category Feeds

Request:

    GET /v1/categories/40/feeds

Response:

Array of [Feed](models.md#feed) objects.

This API endpoint is available since Miniflux v2.0.29.

<a id="endpoint-get-categories"></a>
## Get Categories

Request:

    GET /v1/categories

Response:

```json
[
    {"title": "All", "user_id": 267, "id": 792, "hide_globally": false},
    {"title": "Engineering Blogs", "user_id": 267, "id": 793, "hide_globally": false}
]
```

Since Miniflux 2.0.46, you can pass the argument `?counts=true` to include `total_unread` and `feed_count` in the response:

Request:

    GET /v1/categories?counts=true

Response:

```json
[
  {
    "id": 1,
    "title": "All",
    "user_id": 1,
    "hide_globally": false,
    "feed_count": 7,
    "total_unread": 268
  }
]
```

<a id="endpoint-create-category"></a>
## Create Category

Request:

    POST /v1/categories
    Content-Type: application/json

    {
        "title": "My category"
    }

Response:

``` json
{
    "id": 802,
    "user_id": 267,
    "title": "My category",
    "hide_globally": false
}
```

Since Miniflux 2.2.8, you can also pass the `hide_globally` field when creating a category:

    POST /v1/categories
    Content-Type: application/json

    {
        "title": "My category",
        "hide_globally": true
    }

<a id="endpoint-update-category"></a>
## Update Category

Request:

    PUT /v1/categories/802
    Content-Type: application/json

    {
        "title": "My new title"
    }

Response:

``` json
{
    "id": 802,
    "user_id": 267,
    "title": "My new title",
    "hide_globally": false
}
```

Since Miniflux 2.2.8, you can also pass the `hide_globally` field when updating a category:

    PUT /v1/categories/123
    Content-Type: application/json

    {
        "hide_globally": true
    }

<a id="endpoint-refresh-category"></a>
## Refresh Category Feeds

Request:

    PUT /v1/categories/123/refresh

    - Returns `204` status code for success.
    - Category feeds are refreshed in a background process.

This API endpoint is available since Miniflux v2.0.42.

<a id="endpoint-delete-category"></a>
## Delete Category

Request:

    DELETE /v1/categories/802

Returns a `204` status code when successful.

<a id="endpoint-mark-category-entries-as-read"></a>
## Mark Category Entries as Read

Request:

    PUT /v1/categories/123/mark-all-as-read

Returns `204 No Content` status code for success.

This API endpoint is available since Miniflux v2.0.26.

<a id="endpoint-export"></a>
## OPML Export

Request:

    GET /v1/export

The response is a XML document (OPML file).

This API call is available since Miniflux v2.0.1.

<a id="endpoint-import"></a>
## OPML Import

Request:

    POST /v1/import

    XML data

- The body is your OPML file (XML).
- Returns `201 Created` if imported successfully.

Response:

``` json
{
  "message": "Feeds imported successfully"
}
```

This API call is available since Miniflux v2.0.7.

