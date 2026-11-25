# Root helper without a Developer ID

## Overview

An app that needs root (a daemon that reads all processes or writes in `/Library`) ships a helper. Without a Developer ID, the helper must run from a root-owned copy outside the app bundle. A bundle in `/Applications` is writable by the user, so a helper that runs from it gives root to any user-level code.

## The rule

The root process runs only a file that root owns: `/Library/PrivilegedHelperTools/<helper>` (`root:wheel 755`; the folder is root-only, unlike `/usr/local`) and `/Library/LaunchDaemons/<label>.plist` (`root:wheel 644`) with `ProgramArguments`, not `BundleProgram`. The install copies the helper with `sudo` to `<helper>.new`, checks that root-owned copy against the pinned release certificate, then `mv`s it into place. The install writes the plist from its own text. Root never runs a script or binary from the bundle.

## Evidence: `SMAppService.daemon` without a Team ID (probe on macOS 27)

| Step | Result |
|---|---|
| App calls `register()` | Throws "Operation not permitted", status `requiresApproval` |
| User approves the app entry in Login Items | The helper stays disabled. Login Items lists it separately under its executable name. Log: "Bundle identifiers from launchd plist ignored because the executable doesn't have a Team ID" |
| User turns on the executable item | launchd still fails ("No such process") until the app registers again |
| Swap the helper file with `cp` and `mv`, no password | launchd refuses it: BTM stored a SHA-256 of the executable |
| The genuine app registers again | BTM stores the new checksum, no new approval: the swapped file runs as root |

The app registers at each launch, so the next launch finishes the attack.

## Install paths (all three end the same)

1. `install.sh` (`curl -fsSL https://<domain>/install.sh | sh`, `shipping.md`): attach the DMG read-only, check the app against the pin, copy the app to `/Applications`, then with `sudo` (it reads `/dev/tty`) copy the helper to `.new`, check the root-owned copy, `mv` it into place, write the plist, `launchctl bootout system/<label>` then `launchctl bootstrap system <plist>`.
2. Cask: `postflight` removes quarantine, then `system_command ..., sudo: true` with inline `install`, `codesign`, `launchctl` from the tap's own text. `uninstall launchctl: "<label>", delete: [helper, plist]`.
3. `make install` (dev): the same `sudo install` lines from the build folder. The user runs it; agents never run `sudo` or `launchctl`.

Check a copy: `codesign --verify --strict -R='identifier "<id>" and certificate leaf = H"<sha1>"' <file>`. A code requirement takes only the certificate SHA-1, the same pin the helper uses for XPC. Use `/usr/bin/codesign` and other full paths: `sudo` and the PATH can find other tools first. Check after the copy, on the root-owned file, never before. The pin is text in `install.sh` and the cask (the tap), never read from the release that it checks.

Updates: `brew upgrade` runs the old cask's `uninstall` and the new `postflight`, so the helper updates. A re-run of `install.sh` does the same. Sparkle replaces only the app: the helper stays old until the ping says "Out of date" and the user runs the install line.

System Settings: a plain LaunchDaemon still gets an "Allow in the Background" item and a "Background Items Added" notice, named after the executable, and on by default (expected; check it on the first install). The docs say that turning it off stops the helper.

## XPC

- The helper calls `setCodeSigningRequirement` with `certificate leaf = H"<sha1>"` plus the caller identifiers (app, CLI). It reads its own leaf at start, so one certificate covers app, CLI and helper.
- A ping returns a protocol version. The app shows "Out of date" with the install line when the helper is older.
- The local `make cert` identity can sign anything as the user: accepted for a personal build, not a security boundary.

## Common mistakes

| Mistake | Reality |
|---|---|
| "`SMAppService` gives one prompt and no `sudo`" | Without a Team ID it is a root escalation (table above). One `sudo` at install is the price. |
| "Login Items approval protects the helper" | Approval is per item, and re-registration replaces the checksum. |
| "Login Items shows the app name" | Without a Team ID it shows the executable name. |
| Check the helper in the bundle, then copy it | The user can swap it in between. Check the root-owned copy. |
| Run `install-helper.sh` from the bundle with `sudo` | That is the same escalation. Keep root steps in `install.sh`, the cask or the Makefile. |
| "Test it later" | Probe first: a throwaway app with a 20 s helper that logs its uid, then swap and re-register. Unregister and delete it after. |
