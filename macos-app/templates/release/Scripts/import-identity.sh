#!/bin/sh
# CI only: imports "__APP_NAME__ Self-Signed" from SIGNING_CERTIFICATE_P12 (base64 p12) and SIGNING_CERTIFICATE_PASSWORD
# into a keychain for this run, in the search list, so bundle.sh finds the identity and codesign can use it.
set -e
test -n "$SIGNING_CERTIFICATE_P12" && test -n "$SIGNING_CERTIFICATE_PASSWORD"
KEYCHAIN="$RUNNER_TEMP/signing.keychain-db"
PASS="$(uuidgen)"
security create-keychain -p "$PASS" "$KEYCHAIN"
security set-keychain-settings -lut 3600 "$KEYCHAIN"
security unlock-keychain -p "$PASS" "$KEYCHAIN"
printf '%s' "$SIGNING_CERTIFICATE_P12" | base64 --decode > "$RUNNER_TEMP/identity.p12"
security import "$RUNNER_TEMP/identity.p12" -k "$KEYCHAIN" -P "$SIGNING_CERTIFICATE_PASSWORD" -T /usr/bin/codesign
rm "$RUNNER_TEMP/identity.p12"
security set-key-partition-list -S apple-tool:,apple:,codesign: -s -k "$PASS" "$KEYCHAIN" > /dev/null
security list-keychains -d user -s "$KEYCHAIN" $(security list-keychains -d user | tr -d '"')
