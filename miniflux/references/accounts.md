# Accounts

<a id="endpoint-create-user"></a>
## Create User

Request:

    POST /v1/users
    Content-Type: application/json

    {
        "username": "bob",
        "password": "test123",
        "is_admin": false
    }

Available Fields:

| Field                      | Type        |
| -------------------------- | ----------- |
| `username`                 | `string`    |
| `password`                 | `string`    |
| `google_id`                | `string`    |
| `openid_connect_id`        | `string`    |
| `is_admin`                 | `boolean`   |

Response:

[User](models.md#user) object.

You must be an administrator to create users.

<a id="endpoint-update-user"></a>
## Update User

Request:

    PUT /v1/users/270
    Content-Type: application/json

    {
        "username": "joe"
    }

Available fields:

| Field                      | Type        | Example         |
| -------------------------- | ----------- |-----------------|
| `username`                 | `string`    |                 |
| `password`                 | `string`    |                 |
| `theme`                    | `string`    | "dark_serif"    |
| `language`                 | `string`    | "fr_FR"         |
| `timezone`                 | `string`    | "Europe/Paris"  |
| `entry_sorting_direction`  | `string`    | "desc" or "asc" |
| `stylesheet`               | `string`    |                 |
| `google_id`                | `string`    |                 |
| `openid_connect_id`        | `string`    |                 |
| `entries_per_page`         | `int`       |                 |
| `is_admin`                 | `boolean`   |                 |
| `keyboard_shortcuts`       | `boolean`   |                 |
| `show_reading_time`        | `boolean`   |                 |
| `entry_swipe`              | `boolean`   |                 |

Response:

[User](models.md#user) object.

You must be an administrator to update users.

<a id="endpoint-me"></a>
## Get Current User

Request:

    GET /v1/me

Response:

[User](models.md#user) object.

This API endpoint is available since Miniflux v2.0.8.

<a id="endpoint-get-user"></a>
## Get User

Request:

    # Get user by user ID
    GET /v1/users/270

    # Get user by username
    GET /v1/users/foobar

Response:

[User](models.md#user) object.

You must be an administrator to fetch users.

<a id="endpoint-get-users"></a>
## Get Users

Request:

    GET /v1/users

Response:

Array of [User](models.md#user) objects.

You must be an administrator to fetch users.

<a id="endpoint-delete-user"></a>
## Delete User

Request:

    DELETE /v1/users/270

You must be an administrator to delete users.

<a id="endpoint-mark-user-entries-as-read"></a>
## Mark User Entries as Read

Request:

    PUT /v1/users/123/mark-all-as-read

Returns `204 No Content` status code for success.

This API endpoint is available since Miniflux v2.0.26.

<a id="endpoint-get-api-keys"></a>
## Get API Keys

Request:

    GET /v1/api-keys

Response:

```json
[
    {
        "id": 1,
        "user_id": 1,
        "description": "My API Key",
        "token": "1234567890abcdef1234567890abcdef",
        "created_at": "2023-10-07T03:52:50.013556Z",
        "last_used_at": "2023-10-07T03:52:50.013556Z"
    }
]
```

This endpoint is available since Miniflux 2.2.9.

<a id="endpoint-create-api-key"></a>
## Create API Key

Request:

    POST /v1/api-keys

    {"description": "My API Key"}

Response:

```json
{
    "id": 1,
    "user_id": 1,
    "description": "My API Key",
    "token": "1234567890abcdef1234567890abcdef",
    "created_at": "2023-10-07T03:52:50.013556Z",
    "last_used_at": "2023-10-07T03:52:50.013556Z"
}
```

This endpoint is available since Miniflux 2.2.9.

<a id="endpoint-delete-api-key"></a>
## Delete API Key

Request:

    DELETE /v1/api-keys/1

Returns a `204 No Content` status code for success.

This endpoint is available since Miniflux 2.2.9.

## Source-verified user update fields

The pinned `UserModificationRequest` additionally accepts the following optional fields; minimum versions are not documented in the supplied manual. Theme, language, sorting, and preference values must be valid for the deployed server.

- string: `entry_sorting_order`, `custom_js`, `external_font_hosts`, `gesture_nav`, `display_mode`, `default_home_page`, `categories_sorting_order`, `block_filter_entry_rules`, `keep_filter_entry_rules`.
- int: `default_reading_speed`, `cjk_reading_speed`.
- bool: `mark_read_on_view`, `mark_read_on_media_player_completion`, `always_open_external_links`, `open_external_links_in_new_tab`.
- float64: `media_playback_rate`.

The manual lists `google_id` and `openid_connect_id` for updates, but neither appears in the pinned user-modification request. They are supported on user creation and returned on users; do not assume they can be changed through PUT on this revision. Omitted optional update fields are left unchanged. All user-management routes except `/v1/me` and the authenticated user's own mark-all-as-read require administrator authorization. API keys belong to the authenticated account; never print their returned `token` values.
