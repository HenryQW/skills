#!/bin/sh
# Prints the section of CHANGELOG.md for a version, without its heading. Fails when the section is missing or empty,
# so a release cannot go out with no notes.
# Usage: bash Scripts/changelog.sh <version>
set -e
cd "$(dirname "$0")/.."
NOTES="$(awk -v v="## $1" '$0 == v { on = 1; next } on && /^## / { exit } on' CHANGELOG.md | sed -e '/./,$!d')"
test -n "$NOTES" || { echo "CHANGELOG.md has no section \"## $1\"" >&2; exit 1; }
printf '%s\n' "$NOTES"
