#!/usr/bin/env bash
set -eu

probe_dir="$(mktemp -d)"
trap 'rm -rf "$probe_dir"' EXIT
cat >"$probe_dir/probe.cjs" <<'EOF'
require("node:fs").appendFileSync(process.env.PI_ENTRY_PROBE, `${process.argv[1]}\n`)
EOF
PI_ENTRY_PROBE="$probe_dir/entries" \
  NODE_OPTIONS="--require=$probe_dir/probe.cjs ${NODE_OPTIONS:-}" \
  pi --version >/dev/null

PI_CODING_AGENT_ROOT=
while IFS= read -r entry; do
  candidate="$(dirname "$(realpath "$entry")")"
  while [ "$candidate" != "$(dirname "$candidate")" ]; do
    if node -e 'const p=require(process.argv[1]); process.exit(p.name === "@earendil-works/pi-coding-agent" ? 0 : 1)' \
      "$candidate/package.json" 2>/dev/null; then
      PI_CODING_AGENT_ROOT="$candidate"
      break 2
    fi
    candidate="$(dirname "$candidate")"
  done
done <"$probe_dir/entries"

test -n "$PI_CODING_AGENT_ROOT"
test -d "$PI_CODING_AGENT_ROOT/examples/extensions"
test -f "$PI_CODING_AGENT_ROOT/docs/extensions.md"
printf '%s\n' "$PI_CODING_AGENT_ROOT"
