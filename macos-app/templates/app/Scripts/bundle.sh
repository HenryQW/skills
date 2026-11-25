#!/bin/sh
# All app targets use this recipe. Release workflows use build/ and local make targets use .build/.
set -eu
cd "$(dirname "$0")/.."
mode=${1:-}
case $mode in
    --local) output=.build ;;
    ''|--install) output=build ;;
    *) echo 'usage: bundle.sh [--local|--install]' >&2; exit 2 ;;
esac
swift build -c release
bin=$(swift build -c release --show-bin-path)
app="$output/__APP_NAME__.app"
mkdir -p "$output"
stage=$(mktemp -d "$output/.bundle-__EXEC__.XXXXXX")
trap 'rm -rf "$stage"' EXIT
contents="$stage/__APP_NAME__.app/Contents"
mkdir -p "$contents/MacOS" "$contents/Resources"
cp "$bin/__EXEC__" "$contents/MacOS/"
cp Packaging/Info.plist "$contents/Info.plist"
if [ -d Packaging/Resources ]; then ditto Packaging/Resources "$contents/Resources"; fi
cp Scripts/install-app.sh "$contents/Resources/"
if [ -f Packaging/AppIcon.icns ]; then
    cp Packaging/AppIcon.icns "$contents/Resources/"
    plutil -replace CFBundleIconFile -string AppIcon.icns "$contents/Info.plist"
fi
if [ -e VERSION ]; then
    version=${APP_VERSION:-$(cat VERSION)}
    plutil -replace CFBundleVersion -string "$version" "$contents/Info.plist"
    plutil -replace CFBundleShortVersionString -string "${APP_SHORT_VERSION:-$version}" "$contents/Info.plist"
fi
set -- --options runtime
if plutil -extract SUPublicEDKey raw "$contents/Info.plist" >/dev/null 2>&1; then
    mkdir -p "$contents/Frameworks"
    ditto "$bin/Sparkle.framework" "$contents/Frameworks/Sparkle.framework"
    # Library validation would reject Sparkle in a self-signed or ad hoc app.
    set -- --deep
fi
identity=${IDENTITY:-'__APP_NAME__ Self-Signed'}
if [ "$identity" != - ] && ! security find-identity -p codesigning | grep -F "\"$identity\"" >/dev/null; then identity=-; fi
if [ "$identity" = - ]; then echo 'warning: ad hoc signing cannot preserve permissions across builds.' >&2; fi
codesign --force "$@" --timestamp=none -s "$identity" -i __BUNDLE_ID__ "$stage/__APP_NAME__.app"
sh Scripts/install-app.sh "$stage/__APP_NAME__.app" "$output"
if [ "$mode" = --install ]; then sh Scripts/install-app.sh "$app" /Applications; fi
printf '%s\n' "$app"
