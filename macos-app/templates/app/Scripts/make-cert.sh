#!/bin/bash
# Creates and trusts a self-signed code-signing identity in the login keychain.
set -euo pipefail

NAME="__APP_NAME__ Self-Signed"
KEYCHAIN="$HOME/Library/Keychains/login.keychain-db"

if security find-identity -v -p codesigning | grep -F "$NAME" >/dev/null; then
    echo "Identity '$NAME' already exists."
    exit 0
fi

# A cancelled trust step leaves an untrusted copy; a rerun would make a second one.
if security find-certificate -c "$NAME" "$KEYCHAIN" >/dev/null 2>&1; then
    echo "error: certificate '$NAME' exists but is not valid for code signing." >&2
    echo "Delete the '$NAME' certificate and key in Keychain Access (login keychain), then rerun." >&2
    exit 1
fi

tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT
# System LibreSSL: its default p12 encryption is readable by `security import`.
OPENSSL=/usr/bin/openssl
export P12_PASS
P12_PASS=$("$OPENSSL" rand -hex 16)

"$OPENSSL" req -x509 -newkey rsa:2048 -days 3650 -nodes \
    -subj "/CN=$NAME" \
    -addext "keyUsage=critical,digitalSignature" \
    -addext "extendedKeyUsage=critical,codeSigning" \
    -keyout "$tmp/key.pem" -out "$tmp/cert.pem"

"$OPENSSL" pkcs12 -export -inkey "$tmp/key.pem" -in "$tmp/cert.pem" \
    -name "$NAME" -out "$tmp/id.p12" -passout env:P12_PASS

# codesign may use the key without a prompt, so builds run unattended. Accepted risk: any process of this user can
# also sign as the app.
security import "$tmp/id.p12" -k "$KEYCHAIN" -P "$P12_PASS" -T /usr/bin/codesign

echo "About to trust the certificate for code signing in $KEYCHAIN."
echo "macOS will ask for your login password."
security add-trusted-cert -p codeSign -k "$KEYCHAIN" "$tmp/cert.pem"

if ! security find-identity -v -p codesigning | grep -F "$NAME" >/dev/null; then
    echo "error: identity '$NAME' is not listed after import" >&2
    exit 1
fi
echo "Identity '$NAME' is ready."
