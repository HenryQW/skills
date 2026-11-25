---
title: Install
description: Install __APP_NAME__ on macOS __MIN_MACOS__ with one line in Terminal, with Homebrew, or from the disk image.
---

## Requirements

- macOS __MIN_MACOS__ on a Mac with Apple silicon.

## Install with one line

Open Terminal, paste this line and press Return:

```sh
curl -fsSL https://__HOMEPAGE__/install.sh | sh
```

## Updates

__APP_NAME__ looks for a new version once a day. Settings > Updates has the Stable and Beta channels.

## Other ways to install

### Homebrew

```sh
brew trust --tap __TAP__ && brew install --cask __TAP__/__CASK__
```

### Disk image

Each release has a disk image on the [releases page](https://github.com/__GH_REPO__/releases). macOS says that a copy downloaded with a browser is damaged. Remove the quarantine flag, then open the app:

```sh
xattr -dr com.apple.quarantine /Applications/__APP_NAME__.app && open /Applications/__APP_NAME__.app
```

### Build from source

See [Build from source](/build).
