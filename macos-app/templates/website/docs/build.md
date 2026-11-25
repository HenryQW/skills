---
title: Build from source
description: Build __APP_NAME__ from source, run the tests, and run the docs site.
---

## Requirements

- macOS __MIN_MACOS__ on a Mac with Apple silicon.
- Command Line Tools for Xcode. Run `xcode-select --install` if you do not have them.

## Build and install

```sh
git clone https://github.com/__GH_REPO__.git
cd __GH_NAME__
make cert
make install-app
```

## Other tasks

| Task | Command |
| --- | --- |
| Run the tests | `make test` |
| Run the docs site | `cd website && pnpm install && pnpm dev` |

## The docs site

Cloudflare Pages builds the docs site from `main` at each push: the project runs `pnpm build` in `website` and publishes `website/dist` at [__HOMEPAGE__](https://__HOMEPAGE__).
