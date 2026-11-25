#!/bin/sh
# Installs __APP_NAME__: curl -fsSL https://__HOMEPAGE__/install.sh | sh
# A download with curl gets no quarantine flag, so macOS does not call __APP_NAME__ damaged. The script installs only a
# copy signed with the __APP_NAME__ release certificate, then opens it.
set -eu

URL="https://github.com/__GH_REPO__/releases/latest/download/__EXEC__.dmg"
APP="/Applications/__APP_NAME__.app"
# SHA-256 of the release certificate. Another certificate can have the same name. A new certificate changes it.
CERT="__CERT_SHA256__"

fail() { echo "$1" >&2; exit 1; }
[ "$(uname -m)" = arm64 ] || fail "__APP_NAME__ needs a Mac with Apple silicon."
host_version=$(sw_vers -productVersion)
awk -v host="$host_version" -v minimum="__MIN_MACOS__" 'BEGIN {
    if (host !~ /^[0-9]+([.][0-9]+)*$/) exit 1
    split(host, h, "."); split(minimum, m, ".")
    exit !(h[1]+0 > m[1]+0 || (h[1]+0 == m[1]+0 && h[2]+0 >= m[2]+0))
}' || fail "__APP_NAME__ needs macOS __MIN_MACOS__ or later (found $host_version)."


TMP="$(mktemp -d)"
trap 'hdiutil detach -quiet "$TMP/mnt" 2>/dev/null || true; rm -rf "$TMP"' EXIT

echo "Downloading __APP_NAME__..."
curl -fL --progress-bar "$URL" -o "$TMP/app.dmg"
hdiutil attach -quiet -nobrowse -readonly -mountpoint "$TMP/mnt" "$TMP/app.dmg"

codesign --verify --deep --strict "$TMP/mnt/__APP_NAME__.app" || fail "The download is not valid. Nothing is installed."
codesign -d --extract-certificates="$TMP/cert" "$TMP/mnt/__APP_NAME__.app" 2>/dev/null
[ "$(shasum -a 256 "$TMP/cert0" | cut -d' ' -f1)" = "$CERT" ] || fail "The download is not signed by __APP_NAME__. Nothing is installed."

# The read-only image holds the verified app and its signed install helper.
source="$TMP/mnt/__APP_NAME__.app"
osascript -e 'if application id "__BUNDLE_ID__" is running then tell application id "__BUNDLE_ID__" to quit' 2>/dev/null || true
sh "$source/Contents/Resources/install-app.sh" "$source" /Applications
open "$APP"
echo "__APP_NAME__ is installed."
