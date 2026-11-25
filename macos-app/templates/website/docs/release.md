---
title: Release
description: How a release of __APP_NAME__ is made and put on Homebrew.
---

A tag starts a release. The GitHub Actions workflow `.github/workflows/release.yml` makes it.

## Make a release

1. Write the new version in `VERSION` and its section in `CHANGELOG.md`, and commit them.
2. Tag the commit with the same version, then push the tag:

```sh
git tag v0.2.0
git push origin v0.2.0
```

## Signing

A release is signed with the self-signed certificate "__APP_NAME__ Self-Signed". It has no Developer ID, so Apple does not notarize it.

## The Homebrew tap

The cask is `Casks/__CASK__.rb` in `__TAP_REPO__`. Users install with:

```sh
brew trust --tap __TAP__ && brew install --cask __TAP__/__CASK__
```
