#!/usr/bin/env sh
set -eu

[ "$#" -eq 1 ] || { printf '%s\n' 'usage: verify-pr-target.sh PR' >&2; exit 2; }
exec node scripts/pr-feedback.mjs target --pr "$1"
