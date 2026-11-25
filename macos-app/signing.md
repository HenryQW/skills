# Signing and certificates

## Overview

macOS keeps each privacy permission (Input Monitoring, Accessibility, Screen Recording, Full Disk Access, Automation), login items and Keychain access against the app's designated requirement. An ad hoc signature makes the requirement a `cdhash`, which changes with every build. So each rebuild silently loses every grant. A stable self-signed identity makes the requirement "bundle ID + certificate", which stays the same across builds. Exception: a Keychain item also has a partition list, and for an app with no Team ID (self-signed or ad hoc) each entry is `cdhash:<hash>`. So "Always Allow" lasts only until the next build or update, and then macOS asks for the login password again. Only a Team ID (Developer ID) makes it stable; check with `security dump-keychain -a` (look for the `partition_id` entry) and `codesign -dvvv` (`TeamIdentifier`, `CDHash`).

## Rules

1. **One identity per app, named `<App> Self-Signed`.** The same certificate signs local builds and releases (`shipping.md`). Never sign an app with the identity of another app: it ties the two apps together and hides that the app has no identity of its own.
2. **Make the identity before the first build that the user grants a permission.** `make cert` (`Scripts/make-cert.sh`) changes the login keychain and asks for the login password, so the user runs it. The agent asks, and does not run it.
3. **Do not rebuild between a grant and the check of that grant** while the app is signed ad hoc. The rebuild removes the grant that the user just gave.
4. **The app checks the result of each protected call and says what failed.** For example `IOHIDManagerOpen` returns `kIOReturnNotPermitted`; show that in the window with the fix, not an empty state.
5. **If the app ships, keep the certificate.** The user exports the identity from Keychain Access as a `.p12` into a password manager for CI (`SIGNING_CERTIFICATE_P12`). A new certificate later resets every user's permissions.
6. **An app that already has an identity with another name keeps it.** Renaming it is a new certificate.

## Diagnose a lost permission

| Check | Command |
|---|---|
| The app's requirement | `codesign -d -r- "/Applications/<App>.app"` (a `cdhash H"…"` line means ad hoc) |
| The granted requirement | `sqlite3 "/Library/Application Support/com.apple.TCC/TCC.db" "select hex(csreq), auth_value from access where service='kTCCServiceListenEvent' and client='<bundle id>'"`, then decode the hex with `xxd -r -p \| csreq -r- -t` |
| Signing identities | `security find-identity -v -p codesigning` |

The two requirements differ: the grant belongs to an older build. Services: `kTCCServiceListenEvent` (Input Monitoring), `kTCCServiceAccessibility`, `kTCCServiceScreenCapture`, `kTCCServiceSystemPolicyAllFiles`. Reading `TCC.db` needs Full Disk Access for the shell.

Fix: sign with the app's identity, install, then the user removes the app in System Settings > Privacy & Security with **−**, adds it again with **+**, and reopens it. A toggle off and on does not update the stored requirement.

## Probe apps and macOS 27

- Check `sw_vers` before you name the settings path. On macOS 27.0 to 27.2, use Privacy & Security > Device Control and Data Access. Apple split it into System & App Protection Override and Accessibility in macOS 27.3 beta. Check the installed version and current Apple guidance.
- A probe needs its own permission. A grant to the production app does not grant access to a separate probe process. Check `AXIsProcessTrusted()` inside the probe after the user grants access.
- Sign the probe with its own stable identity before the first grant. One ad hoc probe was rebuilt after its grant; the privacy log reported a code requirement mismatch, and the app was absent from the settings list. Forcing Launch Services registration did not resolve the mismatch. Do not assume the missing list entry proves the cause.
- If an old probe entry cannot be removed through Settings, use a new bundle ID and stable signature for a new probe. Give it a distinct visible name, register it from a visible Applications folder, then ask the user for a new grant. One Settings grant targeted the old bundle ID even though its recorded path resolved to the new app. Compare the grant's client ID with the running process ID in the privacy log. Do not reset privacy permissions without explicit approval.

## Common mistakes

| Mistake | Reality |
|---|---|
| "The permission is on in System Settings, so the app has it" | The entry can hold the requirement of an older build. Compare the requirements. |
| Ad hoc builds while the user tests a permission | Each build loses the grant. Make the identity first. |
| Signing with another app's identity because it is already in the keychain | Each app has its own. Ask the user to run `make cert`. |
| A new certificate to fix a signing problem | Every user grants the permissions again. Keep the first certificate. |
| Reading `_kLSApplicationWouldBeTerminatedByTALKey=1` in the log as "macOS will quit the app" | Long-running apps log it too. It is not evidence of a termination. |
