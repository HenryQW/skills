# Debugging window resizes

A fitted window has two size sources: your fit code and AppKit or SwiftUI layout. A fault shows when they disagree. Log each size change, then let a script flag the abnormal patterns.

Debug-level os_log is not saved to disk, so `log show` cannot find it later. The watch must run while the problem happens.

## Instrument

Use one `Logger(subsystem: "<bundle id>", category: "frame")` and `.debug` lines:

- `content A -> B rows=N filter=X`: content height changed. Add state keys that explain a change.
- `fit h=A -> B sliding=…` and `slideIn h=A -> B visible=…`: each fit or slide request.
- `resized h=H live=L`: each real resize, in `windowDidResize`. `live` is `inLiveResize` (a resize by hand).

Every new `setFrame` or `setContentSize` gets a line with its height, in the form of `fit`. Else the watch flags it as FOREIGN.

## Flags

| Flag | Meaning | Order |
|---|---|---|
| TWICE | one change resized the window twice in 0.1 s (a visible jump) | 1 |
| FOREIGN | a height no fit asked for (1 pt tolerance): minSize, a content minimum, frame autosave, SwiftUI sizing | 2 |
| BURST | 3 or more resizes in 1 s: fit and AppKit fight | 2 |
| RESTART | a slide starts again on an open window with no height change | 3 |
| FLIP | content height A, B, A in 5 s | find what changes between the lines |
| BOUNCE | content down then up (or up then down), 20 pt or more each, in 1 s | compare `rows=` on both lines |

## Steps

1. Build and relaunch the app.
2. Run `bash scripts/watch-frames.sh <subsystem> 10m` (the path is in the skill folder). With Monitor, add `| tee <scratchpad>/frames.log | grep --line-buffered -E '<<|rror'`.
3. Reproduce. For each flag, read the 10 lines before it. Say which line started the change.
4. Fix the cause. Repeat on the same scenario until no flag shows.

## Check without the user

Add a demo scene that makes the change. Wait until `ioreg -c IOHIDSystem | awk '/HIDIdleTime/ {print int($NF/1000000000); exit}'` is 10 or more before you drive the app. Never send keys or move the pointer while the user is active. Run the scene under the watch.

A flag on a `resized` line is a fault. A flag on a `content` line alone is SwiftUI's own layout passes; it is a fault only when TWICE follows it.

## Fixes that worked

- One minimum height shared by the fit and the window `minSize`.
- Set the height in one step. Animate the origin only, never the height.
- Round fitted heights to whole points, so they compare equal.
- Coalesce fits to one per main-loop turn.
- Lay out the window before its first show.
- Do not restart a slide to the same size.
