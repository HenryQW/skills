# AGENTS.md

__APP_NAME__: TODO(scaffold) one line on what it is and its parts (app, helpers, CLI). Read this file first; open other docs only for the part you need.

## Where things are

| Need | File |
|---|---|
| What must be true now | `docs/requirements.md` |
| Why it is built this way (hard-to-reverse choices) | `docs/adr/` (one decision per file) |
| All other decisions, with options and evidence | `docs/decisions/log.md` (append only) |
| How the app should look and feel | `DESIGN.md` |
| Words and their meaning | `GLOSSARY.md` |
| Native Mac checklist for any UI change | `DESIGN.md` › Mac citizen |
| Active plans (delete when done; git keeps them) | `docs/plans/` |
| Resumable state (git-ignored) | `.context/progress.md` |

Code: `Sources/__EXEC__Core` (models, storage, rules; no UI imports), `Sources/__EXEC__` (SwiftUI app). Tests: `Tests/__EXEC__CoreTests`.

## Build and test

- `make test`: the only way to run tests (it passes the Swift Testing plugin path).
- `make app`: builds and signs `.build/__APP_NAME__.app` with the `__APP_NAME__ Self-Signed` identity when the keychain has it, else ad hoc with a warning. An ad hoc build loses every macOS permission (Input Monitoring, Accessibility, login items) at each rebuild.
- `make install-app`: copies the app to `/Applications`. No root.
- `make cert`: changes the login keychain and asks for the user's password. Agents never run it; ask the user before the first build that the user grants a permission. Never sign with another app's identity.
- Linker "search path ... not found" warnings are harmless toolchain noise.

## Toolchain and platform traps

- No SwiftUI macro plugin: `@State`, `@Entry`, `#Preview` do not compile. View state lives in an `@Observable` model that the app owns; views bind it with `@Bindable`. For a one-off value only: `private let _x = State(initialValue: ...)`, read `_x.wrappedValue`, bind `_x.projectedValue`. `@Observable`, `@Bindable`, `@AppStorage`, `@Environment` work.
- No XCTest: tests use Swift Testing (`import Testing`, `@Test`, `#expect`).
- A `MenuBarExtra` app quits when its last window closes unless `applicationShouldTerminateAfterLastWindowClosed` returns false. A menu-bar-only app sets `LSUIElement` in `Packaging/Info.plist`.
- Notifications and login items need the app run from its bundle with the signing identifier equal to the bundle ID; `make app` does that. Dev builds (other ID) have both off.
- A borderless `NSPanel` must override `canBecomeKey`, and its text field gets first responder through AppKit (`makeFirstResponder`); SwiftUI focus does not reach it.
- Key handlers in a text field let keys pass while the input method has marked text (`NSTextView.hasMarkedText()`).
- A global hotkey uses Carbon `RegisterEventHotKey`; it needs no Accessibility permission.
- SwiftUI `.inspector` grows the window; use an in-content pane when the window must not resize.
- A window made in `App.init` does not show: `NSApp` is nil there. Make windows after launch (`DispatchQueue.main.async`).
- The Settings window does not resize: SwiftUI's `Settings` window has no resizable style, whatever `windowResizability` says. The view inserts `.resizable` in its window's `styleMask` (an `NSViewRepresentable` background, in `viewDidMoveToWindow`).
- Values in a grouped `Form` show a text cursor and select: `LabeledContent` values are selectable text there. Set `.textSelection(.disabled)` on the form.
- A hover on a non-activating panel does not give the app focus, and the cooperative `NSApp.activate()` leaves the other app in front. Use `NSApp.activate(ignoringOtherApps: true)` when the app must take focus.
- A window that slides off the screen leaves a strip visible at the end: a spring has a slow tail. Slide off the screen with an ease-in; a spring is only for the slide in.
- The parent of a process is missing when that parent is a root process (such as `login` between a terminal and its shell): `proc_pidinfo` cannot read root processes. Read parents with `sysctl` `KERN_PROC_PID`, as `ps` does.
- `ViewThatFits` does not work inside toolbar items; measure the width instead.
- `windowToolbarStyle` has no effect on the `Settings` scene. Liquid Glass on the toolbar, sidebar and popovers is automatic; add none.
- In zsh, `log` is a builtin: use `/usr/bin/log show`. In agent worktrees, plain `git` can be refused: use `/usr/bin/git`.

## Rules for changes

- TODO(scaffold): the owner's commit rule. Default: every change is committed on a branch and merged after review and acceptance; one concern per commit; no uncommitted work at the end of a task.
- Smallest change that follows the existing code; match comment density and naming.
- Read `DESIGN.md` before a UI change. A specific rule (size, control, label) is a requirement line in `docs/requirements.md`, added in the same commit as the change. Change `DESIGN.md` only when the design language changes.
- Native SwiftUI and AppKit components with default styling first. No custom fonts, colours or backgrounds.
- Every interactive control has an accessibility name; destructive actions have text buttons.
- Docs, plans, reports and UI copy: ASD-STE100 Simplified Technical English, no em or en dashes.
- New decision: add a `D<n>` entry to `docs/decisions/log.md`; add an ADR only if it is hard to reverse, surprising and a real trade-off.
- Models and rules live in `__EXEC__Core` with tests; views stay thin. Menus, shortcuts and toolbar buttons call the same command code.
- Design change: show up to three mockups to choose from, with one marked as recommended (fewer when fewer real options exist). Build only after the user picks one.
- Settings: each setting row has a one-line explanation under its name in the secondary colour. All setting labels share one maximum width, so labels and controls read as two columns.
- Capitals: Title Case for buttons, menu items, picker options, tab names and window titles; sentence case for setting names, toggle labels, explanations, hints and status text.
- Every control that reacts to a click shows a grey hover fill. Hover is grey and selection is the accent; the two never look alike.
- Say each fact once: do not repeat what a section, a filter or a colour already shows.

## Running and checking the app

- For a check, run `make run-dev` in the background. It builds "__APP_NAME__ Dev" (bundle ID `__BUNDLE_ID__.dev`, so Spotlight never opens it instead of the installed app), runs one dev build at a time, and unregisters it when it quits. Quit it by PID (`pgrep -f "__APP_NAME__ Dev.app"`), never `pkill -x`.
- Drive the app through System Events accessibility (`AXPress`, `click menu item`, `size of window 1`); it works in the background. Coordinate clicks do not land reliably. Re-resolve `window 1 of process` each time.
- Screenshots: one window only (`screencapture -x -o -l <window id>`, id from `CGWindowListCopyWindowInfo`); never the full screen; delete after review.
- Dark mode check: relaunch with `--args -AppleInterfaceStyle Dark`; never change the system appearance.
- Never send keys or move the pointer while the user is active (check `HIDIdleTime` in `ioreg -c IOHIDSystem`). Stop automatic checks while the user tests by hand.
- Add a demo mode before the first UI check: `--demo` shows fixed placeholder data and reads or saves no real data or settings; `--demo-scene <name>` opens one named scene, and its window stays open. Screenshots and UI checks use it, so they need no user and no real data.

## Never

`git push` without the user's go-ahead; sudo; launchctl; keychain changes; system settings changes; deleting outside the repo.
