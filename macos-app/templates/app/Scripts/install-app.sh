#!/bin/sh
# Stage the app on the destination volume. A failed copy or verification leaves the installed app in place.
set -eu
source=${1:?source app required}
directory=${2:?destination directory required}
app="$directory/__APP_NAME__.app"
stage=$(mktemp -d "$directory/.install-__EXEC__.XXXXXX")
trap 'rm -rf "$stage"' EXIT
candidate="$stage/__APP_NAME__.app"
ditto "$source" "$candidate"
codesign --verify --deep --strict "$candidate"

# renamex_np swaps two existing directories atomically. On a first install, refuse to overwrite a concurrent install.
flag=4 # RENAME_EXCL
if [ -L "$app" ] || { [ -e "$app" ] && [ ! -d "$app" ]; }; then
    echo "Cannot replace $app: expected an app directory." >&2
    exit 1
elif [ -d "$app" ]; then
    flag=2 # RENAME_SWAP
fi
/usr/bin/osascript -l JavaScript - "$candidate" "$app" "$flag" <<'JS'
ObjC.bindFunction('renamex_np', ['int', ['char *', 'char *', 'unsigned int']]);
function run([source, destination, flag]) {
    if ($.renamex_np(source, destination, Number(flag)) !== 0) {
        throw Error('Could not install ' + destination + '. Check write access and filesystem support.');
    }
}
JS
