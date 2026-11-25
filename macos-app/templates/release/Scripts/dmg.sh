#!/bin/sh
# Pack build/__APP_NAME__.app into build/__EXEC__.dmg, with a link to /Applications to drag it onto and a note on the
# first launch. A release publishes this one file for the download, the Homebrew cask and Sparkle updates.
set -e
cd "$(dirname "$0")/.."
DMG="build/__EXEC__.dmg"
STAGE="$(mktemp -d)"
cp -R "build/__APP_NAME__.app" "$STAGE/"
# macOS calls the downloaded app damaged (no Developer ID, not notarized); this note says how to open it.
cp Packaging/dmg/damaged.txt "$STAGE/Read me if __APP_NAME__ is damaged.txt"
ln -s /Applications "$STAGE/Applications"
rm -f "$DMG"
diskutil image create from --format UDZO --volumeName "__APP_NAME__" "$STAGE" "$DMG" >/dev/null
rm -rf "${STAGE:?}"
echo "$DMG"
