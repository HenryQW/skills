# Shipping a macOS app without a Developer ID

## Overview

A tag `v<VERSION>` makes a signed DMG (disk image), a Sparkle 2 appcast and a cask update. Each push to `main` makes a beta. Without a Developer ID, trust comes from two keys that never change: one self-signed certificate and one Sparkle EdDSA key. Start from an app that `scaffolding.md` made.

## Decide first

| Placeholder | Value |
|---|---|
| `__APP_NAME__`, `__EXEC__`, `__BUNDLE_ID__`, `__MIN_MACOS__` | As in the scaffold |
| `__GH_REPO__`, `__TAP_REPO__` | Public repos `owner/app`, `owner/homebrew-tap` |
| `__CASK__`, `__DESC__`, `__HOMEPAGE__` | Cask token and text |
| `__MACOS_RUNNER__` | Runner with Xcode for `__MIN_MACOS__` |
| Feeds | Stable `SUFeedURL`: `.../releases/latest/download/appcast.xml`; beta: `.../releases/download/beta/appcast.xml` |

## Steps

1. Copy `templates/release/` into the repo and fill the placeholders until `grep -rn '__[A-Z_]*__'` finds none. Add `VERSION`.
2. Add Sparkle as the `Updater.swift` header says. Call `Updater.shared.start()` after launch. Add a Stable/Beta picker and the two automatic toggles. Set `SUPublicEDKey` in `Packaging/Info.plist`. Both local and release builds use the starter’s `Scripts/bundle.sh` and `Scripts/install-app.sh`. Copy these scripts and the Makefile targets into older projects. Put app resources in `Packaging/Resources/`.
3. The release certificate is the app's one identity, `__APP_NAME__ Self-Signed` (`signing.md`). If `make cert` already made it, the user exports it from Keychain Access as a `.p12`; else the user runs `make cert` first. The user keeps the `.p12` and password in a password manager and sets `SIGNING_CERTIFICATE_P12` (base64) and `SIGNING_CERTIFICATE_PASSWORD`. The agent never holds them.
4. The user makes the EdDSA key once: `.build/artifacts/sparkle/Sparkle/bin/generate_keys` prints `SUPublicEDKey`; `-x <file>` exports the private key for `SPARKLE_ED_PRIVATE_KEY`. Before the first release, set the GitHub Actions repository variable `SPARKLE_ED_PUBLIC_KEY` from the original public key. For an existing app, take the key from the last trusted release. Both channels verify against this pin. Plan an explicit Sparkle key migration before changing it.
5. Make `__TAP_REPO__` empty. Set `TAP_TOKEN` (fine-grained, contents write on the tap). Run the Tap token workflow.
6. The one-line install: copy `templates/website/public/install.sh` to `website/public/` (`docs-site.md`). Set `__CERT_SHA256__`: the user runs `codesign -d --extract-certificates=/tmp/c "/Applications/__APP_NAME__.app"` on a release build and `shasum -a 256 /tmp/c0`. A certificate is public; the `.p12` is not. A root helper adds steps (`privileged-helper.md`).
7. Push one `v` tag before the first beta; `beta.yml` needs it.
8. Channels (Stable and Beta): read `channels.md` before you change a workflow, the feeds or the picker.
9. Each release: patch bump by default. Draft the `CHANGELOG.md` section from `bash Scripts/release-notes.sh v<previous> HEAD __GH_REPO__` and the file's rules. Check it, show the user, commit it with `VERSION`, push the tag.

Run scripts as `bash Scripts/x.sh`: a copy can lose the execute bit.

## Traps

| Symptom | Cause | Fix |
|---|---|---|
| Permissions reset, Keychain asks again, Sparkle signature check fails | Ad hoc or new certificate gives a new identity | One certificate for all builds; workflows check `Authority=` |
| Local builds lose permissions | Ad hoc local build | User imports the release `.p12` into the login keychain |
| Sparkle.framework does not load | Hardened runtime library validation | Build with the shared bundle script and set `SUPublicEDKey` in the app plist |
| No installed copy updates | Bad EdDSA signature, the only trust path | `sign_update` from `.build/artifacts`; `verify-update.swift` before publish |
| Beta version `beta.N`, empty notes | `git describe --tags` finds the `beta` tag | Always `--match 'v*'` |
| Old version right after publish | GitHub's CDN kept the old `appcast.xml` 30 to 90 s | Wait two minutes |
| Cask stays old | `TAP_TOKEN` expired | Token check before publish, and weekly |
| "App is damaged" | Quarantine flag, no notarization | `xattr -dr com.apple.quarantine /Applications/<App>.app` (DMG note, install docs); cask `postflight` |

## Common mistakes

- A beta as latest release: keep `--prerelease --latest=false`.
- Commit lists as release notes: write the section by hand; `release.yml` stops without it. Betas keep the commit list.
- A new certificate as a fix: every user grants permissions again.
- `Scripts/` and `scripts/` in one repo: Linux jobs see case.
- The official Homebrew casks: they need a Developer ID and notarization.
