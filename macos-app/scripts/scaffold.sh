#!/bin/bash
# Copies the templates into an empty folder and fills in the app's names.
# Usage: scaffold.sh <dest> "<App Name>" <Executable> <bundle.id> <min-macos>
set -euo pipefail

if [ $# -ne 5 ]; then
    echo "usage: scaffold.sh <dest> \"<App Name>\" <Executable> <bundle.id> <min-macos>" >&2
    exit 2
fi
dest=$1 name=$2 exec=$3 bundle=$4 macos=$5

[[ "$name" =~ ^[A-Za-z0-9][A-Za-z0-9.\ -]*$ ]] || { echo "error: start the app name with a letter or digit; use letters, digits, spaces, dots or hyphens" >&2; exit 2; }
[[ "$exec" =~ ^[A-Za-z][A-Za-z0-9]*$ ]] || { echo "error: executable must be letters and digits, starting with a letter" >&2; exit 2; }
[[ "$bundle" =~ ^[A-Za-z0-9-]+(\.[A-Za-z0-9-]+)+$ ]] || { echo "error: bundle ID must be reverse DNS, like com.example.app" >&2; exit 2; }
[[ "$macos" =~ ^[0-9]+(\.[0-9]+)?$ ]] || { echo "error: minimum macOS must be like 27 or 27.0" >&2; exit 2; }
[[ "$macos" == *.* ]] || macos="$macos.0"

if [ -e "$dest" ] && [ -n "$(ls -A "$dest")" ]; then
    echo "error: $dest is not empty" >&2
    exit 1
fi

src="$(cd "$(dirname "$0")/../templates/app" && pwd)"
mkdir -p "$dest"
cp -R "$src"/. "$dest"/
lower=$(printf '%s' "$exec" | tr '[:upper:]' '[:lower:]')

find "$dest" -type f -print0 | while IFS= read -r -d '' f; do
    # Apply substitutions only to the text formats in this template.
    case ${f##*/} in *.swift|*.sh|*.plist|*.md|Makefile) ;; *) continue ;; esac
    sed -i '' -e "s|__APP_NAME__|$name|g" -e "s|__EXEC__|$exec|g" -e "s|__EXEC_LOWER__|$lower|g" \
        -e "s|__BUNDLE_ID__|$bundle|g" -e "s|__MIN_MACOS__|$macos|g" "$f"
done
# Deepest paths first, so a renamed folder does not break the paths under it.
find "$dest" -depth -name '*__EXEC__*' -print0 | while IFS= read -r -d '' p; do
    mv "$p" "$(dirname "$p")/$(basename "$p" | sed "s|__EXEC__|$exec|g")"
done
chmod +x "$dest"/Scripts/*.sh

echo "Scaffolded $name in $dest"
echo "Next: fill every TODO(scaffold) line, then make test && make app"
grep -rln "TODO(scaffold)" "$dest" | sed "s|^$dest/|  |"
