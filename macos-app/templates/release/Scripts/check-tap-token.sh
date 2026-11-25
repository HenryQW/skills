#!/bin/sh
# Fails if TAP_TOKEN (the release workflow's token for __TAP_REPO__) does not work, or expires in fewer than
# <days> days. GitHub gives a token's expiry in the github-authentication-token-expiration header; a token without
# one does not expire. Usage: TAP_TOKEN=... bash Scripts/check-tap-token.sh <days>
set -e
test -n "$TAP_TOKEN" || { echo "TAP_TOKEN is not set."; exit 1; }
HEADERS="$(mktemp)"
trap 'rm -f "$HEADERS"' EXIT
STATUS="$(curl -s -o /dev/null -D "$HEADERS" -w '%{http_code}' -H "Authorization: Bearer $TAP_TOKEN" \
    -H "Accept: application/vnd.github+json" https://api.github.com/repos/__TAP_REPO__)"
test "$STATUS" = 200 || { echo "TAP_TOKEN cannot read __TAP_REPO__ (HTTP $STATUS): make a new token and set the secret again."; exit 1; }
EXPIRY="$(sed -n 's/^github-authentication-token-expiration: *//Ip' "$HEADERS" | tr -d '\r')"
if [ -z "$EXPIRY" ]; then echo "TAP_TOKEN works and does not expire."; exit 0; fi
DAYS="$(python3 -c 'import sys, datetime as d; e = d.datetime.strptime(sys.argv[1].replace(" UTC", " +0000"), "%Y-%m-%d %H:%M:%S %z"); print((e - d.datetime.now(d.timezone.utc)).days)' "$EXPIRY")"
if [ "$DAYS" -lt "$1" ]; then
    echo "TAP_TOKEN expires on $EXPIRY, in $DAYS days: make a new token and set the secret again (the release doc)."
    exit 1
fi
echo "TAP_TOKEN works and expires on $EXPIRY, in $DAYS days."
