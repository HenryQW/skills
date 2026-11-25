# Scaffolding a macOS app

## Overview

A new Mac app starts with four required files (`README.md`, `AGENTS.md`, `DESIGN.md`, `GLOSSARY.md` at the repo root) and a build that runs from the shell with Command Line Tools only. The design style is Apple native, minimalist and not flashy. `scripts/scaffold.sh` copies the templates and fills in the names, so you write product facts, not boilerplate.

## Before you run anything, decide

| Value | Rule | Example |
|---|---|---|
| App name | Start with a letter or digit. Use letters, digits, spaces, dots or hyphens | `Tide Log` |
| Executable | Letters and digits, starts with a letter | `TideLog` |
| Bundle ID | Reverse DNS | `com.example.tidelog` |
| Minimum macOS | Major or major.minor | `27.0` |
| Archetype | One of the four below | utility |

| Archetype | Window model | Add to the starter app |
|---|---|---|
| Document | `DocumentGroup`, open/save/revert | File menu works by default |
| Library + detail | `NavigationSplitView`, sidebar + content | Sidebar items, ⌘F search |
| Utility | One `WindowGroup` | ⌘N for the main action |
| Menu bar only | `MenuBarExtra`; no main window, no Dock icon | `LSUIElement` true in `Packaging/Info.plist` |
| Window + menu bar item | `WindowGroup` and `MenuBarExtra`; Dock icon stays | `LSUIElement` not set; keep the app alive after the last window closes (see AGENTS traps) |

Ask the user for any value you cannot infer. Do not guess the bundle ID domain.

## Steps

1. `bash <skill-directory>/scripts/scaffold.sh <dest> "<App Name>" <Executable> <bundle.id> <min-macos>`
   It refuses a folder that is not empty.
2. Fill every `TODO(scaffold)` line with product facts: README facts, AGENTS summary, DESIGN Character, GLOSSARY terms, requirement lines. Keep the house principles in `DESIGN.md` as they are.
3. Change the starter app to the archetype. Put models and rules in `<Executable>Core` (no UI imports), views in `<Executable>`.
4. `make test`, then `make app`. Both must pass.
5. `grep -rn "TODO(scaffold)" <dest>` returns nothing. If `<dest>` is not in a git repo, run `git init`. Commit when the user's rules allow commits; otherwise leave the files uncommitted and say so.
6. Before you call any UI done, check it against `mac-citizen.md`.

When the app reads other processes, follow `process-inspection.md`. For releases, read `shipping.md`.

## Toolchain traps (Command Line Tools, no Xcode)

| Symptom | Cause | Fix (already in the templates) |
|---|---|---|
| `@State`, `@Entry`, `#Preview`: "external macro implementation type could not be found" | No SwiftUI macro plugin | View state in an `@Observable` model that the app owns; bind with `@Bindable`. For a one-off value only: `private let _x = State(initialValue: v)`, read `_x.wrappedValue`, bind `_x.projectedValue`. `@Observable`, `@Bindable`, `@Environment`, `@AppStorage` work |
| `@Test`: "plugin for module 'TestingMacros' not found" | `swift test` misses the plugin path | Always `make test` |
| `no such module 'XCTest'` | XCTest is not in Command Line Tools | Swift Testing only |
| `ld: warning: search path ... not found` | Toolchain noise | Ignore |
| Notifications or login items do nothing | Not run from a bundle, or signing identifier is not the bundle ID | `make app`; `codesign -i <bundle id>` is in the Makefile |

## Common mistakes

- `DESIGN.md` in `docs/`: the four required files live at the repo root.
- Fixing a build by trial and error: read the traps table first.
- Custom colours, backgrounds or glass on content: see the principles in `DESIGN.md`.
- A full-screen screenshot to check the UI: capture one window only (`AGENTS.md`).
- A product rule written only in a chat or a plan: it goes into `docs/requirements.md` in the same commit.
