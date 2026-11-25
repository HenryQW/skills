# __APP_NAME__

TODO(scaffold): one paragraph. What the app does for the user, its main screens or surfaces, and any helper or command line tool.

## Requirements

- macOS __MIN_MACOS__ or later
- Command Line Tools (Xcode is not necessary)

## Build and test

```
make build
make test
```

## Install

1. Run `make cert` one time. It adds the `__APP_NAME__ Self-Signed` code-signing certificate to your login keychain, so macOS permissions, notifications and login items keep working across builds. macOS asks for your login password. `make app` then uses it.
2. Run `make install-app`. It builds the app and copies it to `/Applications`.

## What is installed where

| Item | Path |
|---|---|
| App | `/Applications/__APP_NAME__.app` |
| App settings | `defaults read __BUNDLE_ID__` |
| TODO(scaffold): data files, if any | TODO(scaffold) |

## Permissions

TODO(scaffold): each permission the app asks for (notifications, files, accessibility), why, and what does not work without it. Write "None" if there are none.

## Privacy

TODO(scaffold): what the app stores, where, for how long, and whether any data leaves the Mac.

## Troubleshooting

- Read the logs of the last 10 minutes:

  ```
  log show --predicate 'subsystem == "__BUNDLE_ID__"' --last 10m
  ```

## Uninstall

```
rm -rf "/Applications/__APP_NAME__.app"
defaults delete __BUNDLE_ID__
```

TODO(scaffold): add the data paths above, or say that there are none.

## License

TODO(scaffold): the license, or "The owner has not chosen a license yet."
