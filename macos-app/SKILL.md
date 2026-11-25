---
name: macos-app
description: Use when building, debugging or shipping a native macOS app (SwiftUI or AppKit; window, document, library, utility, menu bar or background app). Triggers include starting an app in an empty folder, a Mac with Command Line Tools only and no Xcode, a macOS repo with no README, AGENTS, DESIGN or GLOSSARY file, a UI review against Mac conventions, an app that reads other processes (parent pid, executable path, arguments), a first release without an Apple Developer ID, Sparkle updates, a Stable and Beta update channel, a Homebrew cask, release notes, "permissions reset after update", "Keychain asks again", a code-signing certificate or identity, a permission lost after a rebuild, a window that jumps, shrinks and grows back, flickers or resizes in a loop, a helper or daemon that runs as root, SMAppService or a LaunchDaemon, history stored in SQLite with high disk writes, and a docs site or a one-line install script.
---

# macOS app

One skill for the life of a native Mac app: make it, check it, debug it, ship it. Read this page, then only the file for your situation. Each file stands alone.

| Situation | Read |
|---|---|
| New app, empty folder, or a repo without the four root files | `scaffolding.md` |
| Toolchain errors with Command Line Tools only (`@State`, `@Test`, `XCTest`) | `scaffolding.md` (traps table) |
| Platform traps (`NSApp` nil, Settings window size, panel focus, slide animation) | `templates/app/AGENTS.md` (traps list) |
| A UI change is ready, before you call it done | `mac-citizen.md` |
| The app reads other processes | `process-inspection.md` |
| Signing identity, a permission (Input Monitoring, Accessibility, Screen Recording) lost after a rebuild, an app that gets no events while its permission shows on | `signing.md` |
| First release, Sparkle, DMG, Homebrew cask, release notes | `shipping.md` |
| Stable and Beta update channels | `channels.md` (after `shipping.md`) |
| A window changes size by itself | `window-resizes.md` |
| A helper or daemon that runs as root, `SMAppService.daemon`, a LaunchDaemon, XPC between app and helper | `privileged-helper.md` |
| History recorded every few seconds for weeks (SQLite, one writer), disk writes too high | `history-storage.md` |
| A docs site, the one-line `install.sh`, and an app icon | `docs-site.md` |

## Layout

- `scripts/scaffold.sh`: makes a new app from `templates/app/`.
- `scripts/watch-frames.sh`: streams a window's frame log and flags abnormal resizes.
- `templates/app/`: the starter app (Package.swift, Makefile, the four root files, Sources, Tests, docs).
- `templates/release/`: the release scripts, workflows, cask, Sparkle updater and icon renderer. Copy them in when the app needs its first release, not at scaffold time.
- `templates/website/`: the docs site and `public/install.sh`.

## Rules for every file

- Placeholders: `__APP_NAME__`, `__EXEC__`, `__BUNDLE_ID__`, `__MIN_MACOS__`, and in release templates also `__GH_REPO__`, `__TAP_REPO__`, `__CASK__`. Fill all until `grep -rn '__[A-Z_]*__'` finds none.
- Run scripts as `bash <path>`: a copy can lose the execute bit.
- Never send keys or move the pointer while the user is active (check `HIDIdleTime`). Screenshots are of one window only.
- The user creates and holds secrets (certificates, `.p12` passwords, the Sparkle private key, tokens). The agent never reads or prints them.
