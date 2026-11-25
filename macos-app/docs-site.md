# A docs site for a macOS app

## Overview

The site is a home page and docs pages. It uses blume (a docs generator built on Astro), pnpm, and Cloudflare Pages. The home Hero has the app name, `__DESC__`, an install command with a copy button, and three feature cards. The docs pages are overview, install, how it works, build, release, privacy and glossary, as the app needs. Start from an app that `scaffolding.md` made.

## Decide first

| Placeholder | Value |
|---|---|
| `__APP_NAME__`, `__EXEC__`, `__MIN_MACOS__`, `__DESC__` | As in the scaffold; `__EXEC__` names the npm package `__EXEC__-docs` |
| `__GH_REPO__`, `__GH_OWNER__`, `__GH_NAME__` | `owner/app`, then its two halves (`blume.config.ts` wants them apart) |
| `__CASK__`, `__TAP__` | Cask token; tap name `owner/tap` (the repo is `owner/homebrew-tap`) |
| `__HOMEPAGE__` | The domain only, with no `https://`, for example `app.example.com` |
| `__FEATURE_1__` to `__FEATURE_3__` and `_TEXT__` | Three card titles and one sentence each, in `pages/index.astro` |

## Steps

1. Copy `templates/website/` to `website/`. Fill the placeholders until `grep -rn '__[A-Z_0-9]*__'` finds none.
2. Know each file. `package.json`: scripts and pinned versions. `blume.config.ts`: title, footer, logo, site URL, GitHub repo, sidebar order, colours. `theme.css`: sets the home page width. `components/Hero.astro`: the Hero. `pages/index.astro`: the home page and cards. `docs/*.md`: one page each, with `title` and `description` front matter. `public/`: `icon.png`, `install.sh`.
3. Write the docs pages. Add each new page to `navigation.sidebar` in `blume.config.ts`. The install page and the Hero show the same command. `release.md` and `build.md` keep the facts of `shipping.md` and the Makefile.
4. The app icon: copy `templates/release/Scripts/make-icon.swift`, draw the mark in `drawMark`, run `swift Scripts/make-icon.swift` from the repo root. It writes `Packaging/AppIcon.icns` and `website/public/icon.png`. The `logo` in `blume.config.ts` and the Hero use `/icon.png`.
5. `public/install.sh` is the script that the install page and the Hero run; set it up with `shipping.md` step 6. The Hero command is `curl -fsSL https://__HOMEPAGE__/install.sh | sh`.
6. Run it: `cd website && pnpm install && pnpm dev`. Before you push: `pnpm build` (it writes `dist/`), and `pnpm validate` for a strict check. Do not commit `node_modules`, `dist` or `.blume`.
7. Cloudflare Pages: connect the GitHub repo, production branch `main`, root directory `website`, build command `pnpm build`, output directory `dist`. Each push to `main` deploys. Add the custom domain `__HOMEPAGE__` in the project. The user does this in the dashboard.
8. Say in `build.md` how the site deploys (the template has the paragraph), and in the README how to run it.

## Traps

| Symptom | Cause | Fix |
|---|---|---|
| Build fails on Cloudflare, local build works | Wrong root directory, or the Node or pnpm version differs | Root `website`; versions come from `engines` and `packageManager` in `package.json` |
| A page is not in the sidebar | It is missing from `navigation.sidebar` | Add its path, for example `/privacy` |
| The Hero command fails | `__HOMEPAGE__` has `https://`, or `install.sh` is not in `public/` | Domain only; add the script |
| Old links 404 after a page rename | No redirect | Add `public/_redirects` lines, `/old /new 301` |

## Common mistakes

- Copy that names the app in the template: fill every placeholder, then read each page once.
- A screenshot or personal photo copied from an example site: the template has none; add your own.
- Two sources of the install command: change the Hero, `install.md` and `install.sh` together.
- Prose in docs that is not ASD-STE100 or has em or en dashes.
