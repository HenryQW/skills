#!/usr/bin/env sh
set -eu

[ "$#" -le 1 ] || { printf '%s\n' 'usage: verify-pr-target.sh [PR]' >&2; exit 2; }
script_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
if [ "$#" -eq 0 ]; then
  exec node "$script_dir/pr-feedback.mjs" target
fi
exec node "$script_dir/pr-feedback.mjs" target --pr "$1"
