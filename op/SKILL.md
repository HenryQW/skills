---
name: op
description: Use when reading, searching, editing, tagging, moving, or bulk-updating 1Password items, vaults, or secret references with the `op` CLI, or when `op` reports "account is not signed in" or "multiple accounts found".
---

# op

`op` is the 1Password CLI. Items hold secrets, so every command either reads metadata, reads secrets, or rewrites an item. Pick the narrowest one and keep secrets out of arguments, files, and output.

## Connect

- Run `op account list`. With more than one account, pass `--account <sign-in address>` on every command or set `OP_ACCOUNT`.
- "account is not signed in" while the desktop app is unlocked means the sandbox blocks the app integration socket. Rerun outside the sandbox; do not run `op signin` for it.
- Run `op <command> --help` before using a flag you have not verified. Trust live help over memory.

## Read

| Need | Command | Secrets in output |
|---|---|---|
| Inventory: id, title, vault, category, tags, URLs | `op item list --format json` | No |
| Filter server-side | `--vault`, `--tags`, `--categories`, `--include-archive` | No |
| One item, all fields | `op item get <id> --format json` | Concealed unless `--reveal` |
| One value | `op read 'op://<vault>/<item>/<field>'` | Yes |
| Secrets into a process or file | `op run`, `op inject` | Only to the target |

- Save the `op item list` output once to a scratch file and filter it with `jq`. It holds no secrets, and it saves one API call per item.
- Use item IDs, not titles. Titles are not unique.
- Match IPs and hosts with boundaries, for example `(^|[^0-9])10\.0\.0\.3([^0-9]|$)`. A plain substring also matches `110.0.0.3`.

## Write

| Change | Command | Effect |
|---|---|---|
| Title, primary URL, favorite | `op item edit <id> --title/--url/--favorite` | `--url` sets only the primary URL |
| Tags | `op item edit <id> --tags a,b` | Replaces all tags. Merge with current tags first |
| Built-in or custom field | `op item edit <id> 'section.field[type]=value'` | Arguments are visible to other processes. No secret values here |
| Secondary URLs, many fields, secrets | `op item get <id> --format json \| jq '<change>' \| op item edit <id>` | Replaces the whole item from JSON |
| Vault | `op item move <id> --current-vault A --destination-vault B` | New item ID. Changes who has access |
| Preview | add `--dry-run` to `op item edit` | No change |

- Pipe JSON, do not write it to disk: `op item get` JSON contains secret values.
- JSON edits overwrite passkeys. `op` cannot show if an item has a passkey. Before a JSON edit on a login that can have a passkey, ask the user, or use flag edits.
- After each write, read the item again and compare the changed fields. Item history in the app restores a bad edit.

## Bulk changes

1. Inventory once, filter with `jq`, and show the list of item IDs and the planned change.
2. Get approval before you edit, move, or delete items in bulk. Moves and deletes change IDs and access.
3. Apply each change to one item ID at a time, in sequence. Parallel writes to one vault fail with `(409) Conflict`. Each edit takes 2-11 s, so run long batches in the background with a log.
4. Re-run the inventory filter against live `op item list` output. It must return no remaining matches. Retry only the items that differ.

The CLI cannot edit SSH Key items ("SSH Key item editing in the CLI is not yet supported") or items with a "Sign in with" field ("unsupported field type: ssoLogin"). List these for the user to change in the app.

## Tags

- Use `/` for nested tags, for example `home/nas`. The app shows them as a tree.
- Tags group items across vaults. Vaults control access and sharing. Use vaults for who can see an item, and tags for what it is.
