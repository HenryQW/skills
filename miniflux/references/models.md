# Shared response models

Examples are shapes, not exhaustive schemas or writable-field lists. IDs are integers; response timestamps are RFC 3339 strings (query timestamps are Unix seconds). Optional collections may be null or empty. Never expose nested feed credentials.

## Feed

```json
{
    "id": 42,
    "user_id": 123,
    "title": "Example Feed",
    "site_url": "http://example.org",
    "feed_url": "http://example.org/feed.atom",
    "checked_at": "2017-12-22T21:06:03.133839-05:00",
    "etag_header": "KyLxEflwnTGF5ecaiqZ2G0TxBCc",
    "last_modified_header": "Sat, 23 Dec 2017 01:04:21 GMT",
    "parsing_error_message": "",
    "parsing_error_count": 0,
    "scraper_rules": "",
    "rewrite_rules": "",
    "crawler": false,
    "blocklist_rules": "",
    "keeplist_rules": "",
    "user_agent": "",
    "username": "",
    "password": "",
    "disabled": false,
    "ignore_http_cache": false,
    "fetch_via_proxy": false,
    "category": {
        "id": 793,
        "user_id": 123,
        "title": "Some category"
    },
    "icon": {
        "feed_id": 42,
        "icon_id": 84
    }
}
```

## Entry

```json
{
  "id": 1790,
  "user_id": 1,
  "feed_id": 21,
  "status": "unread",
  "hash": "22a6795131770d9577c91c7816e7c05f78586fc82e8ad0881bce69155f63edb6",
  "title": "New title",
  "url": "https://miniflux.app/releases/1.0.1.html",
  "comments_url": "",
  "published_at": "2013-03-20T00:00:00Z",
  "created_at": "2023-10-07T03:52:50.013556Z",
  "changed_at": "2023-10-07T03:52:50.013556Z",
  "content": "Some text",
  "author": "Frédéric Guillot",
  "share_code": "",
  "starred": false,
  "reading_time": 1,
  "enclosures": [],
  "feed": {
    "id": 21,
    "user_id": 1,
    "feed_url": "https://miniflux.app/feed.xml",
    "site_url": "https://miniflux.app",
    "title": "Miniflux",
    "checked_at": "2023-10-08T23:56:44.853427Z",
    "next_check_at": "0001-01-01T00:00:00Z",
    "etag_header": "",
    "last_modified_header": "",
    "parsing_error_message": "",
    "parsing_error_count": 0,
    "scraper_rules": "",
    "rewrite_rules": "",
    "crawler": false,
    "blocklist_rules": "",
    "keeplist_rules": "",
    "urlrewrite_rules": "",
    "user_agent": "",
    "cookie": "",
    "username": "",
    "password": "",
    "disabled": false,
    "no_media_player": false,
    "ignore_http_cache": false,
    "allow_self_signed_certificates": false,
    "fetch_via_proxy": false,
    "category": {
      "id": 2,
      "title": "000",
      "user_id": 1,
      "hide_globally": false
    },
    "icon": {
      "feed_id": 21,
      "icon_id": 11
    },
    "hide_globally": false,
    "apprise_service_urls": ""
  },
  "tags": []
}
```

## User

```json
{
    "id": 1,
    "username": "admin",
    "is_admin": true,
    "theme": "dark_serif",
    "language": "en_US",
    "timezone": "America/Vancouver",
    "entry_sorting_direction": "desc",
    "stylesheet": "",
    "google_id": "",
    "openid_connect_id": "",
    "entries_per_page": 100,
    "keyboard_shortcuts": true,
    "show_reading_time": true,
    "entry_swipe": true,
    "last_login_at": "2021-01-05T04:51:45.118524Z"
}
```

## Source-verified response field inventory

The following is the full JSON field inventory of the pinned Feed, Entry, and User models. Fields and nullability can vary by release; optional pointers or `omitempty` fields may be absent/null. These are **response** contracts, not mutation payloads. Go `time.Time` values serialize as timestamps, `int64` as integer IDs, and `float64` as numbers. Feed/category/icon/enclosure objects use the shapes in the resource references.

### Feed fields

- int64: `id`, `user_id`.
- string: `feed_url`, `site_url`, `title`, `description`, `language`, `etag_header`, `last_modified_header`, `parsing_error_message`, `scraper_rules`, `rewrite_rules`, `blocklist_rules`, `keeplist_rules`, `block_filter_entry_rules`, `keep_filter_entry_rules`, `urlrewrite_rules`, `user_agent`, `cookie`, `username`, `password`, `apprise_service_urls`, `webhook_url`, `ntfy_topic`, `proxy_url`.
- time.Time: `checked_at`, `next_check_at`.
- int: `parsing_error_count`, `ntfy_priority`, `pushover_priority`.
- bool: `disabled`, `no_media_player`, `ignore_http_cache`, `allow_self_signed_certificates`, `fetch_via_proxy`, `hide_globally`, `disable_http2`, `pushover_enabled`, `ntfy_enabled`, `crawler`, `ignore_entry_updates`.
- Category: `category`.
- FeedIcon: `icon`.
- Entries: `entries`.

### Entry fields

- int64: `id`, `user_id`, `feed_id`.
- string: `status`, `hash`, `title`, `url`, `comments_url`, `language`, `content`, `author`, `share_code`.
- time.Time: `published_at`, `created_at`, `changed_at`.
- bool: `starred`.
- int: `reading_time`.
- EnclosureList: `enclosures`.
- Feed: `feed`.
- []string: `tags`.

### User fields

- int64: `id`.
- string: `username`, `theme`, `language`, `timezone`, `entry_sorting_direction`, `entry_sorting_order`, `stylesheet`, `custom_js`, `external_font_hosts`, `google_id`, `openid_connect_id`, `gesture_nav`, `display_mode`, `default_home_page`, `categories_sorting_order`, `block_filter_entry_rules`, `keep_filter_entry_rules`.
- int: `entries_per_page`, `default_reading_speed`, `cjk_reading_speed`.
- time.Time: `last_login_at`.
- float64: `media_playback_rate`.
- bool: `mark_read_on_view`, `mark_read_on_media_player_completion`, `always_open_external_links`, `open_external_links_in_new_tab`, `keyboard_shortcuts`, `show_reading_time`, `entry_swipe`, `is_admin`.
