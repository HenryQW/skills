# Shared response models

Full JSON field inventory of the pinned Feed, Entry, and User **response** models; these are not writable-field lists. Fields and nullability vary by release; optional pointers or `omitempty` fields may be absent/null, and optional collections may be null or empty. IDs are integers; response timestamps are RFC 3339 strings (query timestamps are Unix seconds). Category, icon, and enclosure shapes are in the resource references. Never expose nested feed credentials.

## Feed

- int64: `id`, `user_id`.
- string: `feed_url`, `site_url`, `title`, `description`, `language`, `etag_header`, `last_modified_header`, `parsing_error_message`, `scraper_rules`, `rewrite_rules`, `blocklist_rules`, `keeplist_rules`, `block_filter_entry_rules`, `keep_filter_entry_rules`, `urlrewrite_rules`, `user_agent`, `cookie`, `username`, `password`, `apprise_service_urls`, `webhook_url`, `ntfy_topic`, `proxy_url`.
- time.Time: `checked_at`, `next_check_at`.
- int: `parsing_error_count`, `ntfy_priority`, `pushover_priority`.
- bool: `disabled`, `no_media_player`, `ignore_http_cache`, `allow_self_signed_certificates`, `fetch_via_proxy`, `hide_globally`, `disable_http2`, `pushover_enabled`, `ntfy_enabled`, `crawler`, `ignore_entry_updates`.
- Category: `category`.
- FeedIcon: `icon`.
- Entries: `entries`.

## Entry

- int64: `id`, `user_id`, `feed_id`.
- string: `status`, `hash`, `title`, `url`, `comments_url`, `language`, `content`, `author`, `share_code`.
- time.Time: `published_at`, `created_at`, `changed_at`.
- bool: `starred`.
- int: `reading_time`.
- EnclosureList: `enclosures`.
- Feed: `feed`.
- []string: `tags`.

## User

- int64: `id`.
- string: `username`, `theme`, `language`, `timezone`, `entry_sorting_direction`, `entry_sorting_order`, `stylesheet`, `custom_js`, `external_font_hosts`, `google_id`, `openid_connect_id`, `gesture_nav`, `display_mode`, `default_home_page`, `categories_sorting_order`, `block_filter_entry_rules`, `keep_filter_entry_rules`.
- int: `entries_per_page`, `default_reading_speed`, `cjk_reading_speed`.
- time.Time: `last_login_at`.
- float64: `media_playback_rate`.
- bool: `mark_read_on_view`, `mark_read_on_media_player_completion`, `always_open_external_links`, `open_external_links_in_new_tab`, `keyboard_shortcuts`, `show_reading_time`, `entry_swipe`, `is_admin`.
