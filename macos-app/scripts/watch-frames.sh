#!/bin/sh
# Watches a window's size changes (the `frame` debug log) and flags abnormal ones as they happen:
#   TWICE    two height changes in 0.1 s, not by hand: one change resized the window twice (the user sees a jump).
#   BURST    3 or more height changes in 1 s, not by hand: the window resizes in a loop.
#   RESTART  a slide that starts again on an open window with no height change: the slide can stutter.
#   FOREIGN  a height that no fit or slide asked for, not by hand: something other than the fit code resized it.
#   FLIP     the content height goes A -> B -> A in 5 s: SwiftUI layout swings between two heights.
#   BOUNCE   the content height goes down then up (or up then down), 20 pt or more each, in 1 s: one step shows a wrong height.
#   FLIP, BOUNCE, TWICE and BURST need the same rows and filter on each step, so a new row or a tile click is not a fault.
# Usage: watch-frames.sh <subsystem> [timeout, e.g. 2m] (default 10m); the category is $FRAME_CATEGORY (default frame).
# Run it, use the app, read the flags. Debug messages are not saved to disk, so this must run while the problem happens.
# watch-frames.sh <file.ndjson> checks saved `log stream --style ndjson` lines instead.
[ -n "${1:-}" ] || { echo "usage: watch-frames.sh <subsystem|file.ndjson> [timeout]" >&2; exit 2; }
if [ -f "$1" ]; then cat "$1"; else
/usr/bin/log stream --level debug --style ndjson --timeout "${2:-10m}" \
    --predicate "subsystem == \"$1\" AND category == \"${FRAME_CATEGORY:-frame}\""
fi |
python3 -I -u -c '
import json, re, sys
from datetime import datetime
resizes, contents, asked = [], [], set()
def t(e): return datetime.strptime(e["timestamp"][:26], "%Y-%m-%d %H:%M:%S.%f").timestamp()
for line in sys.stdin:
    try: e = json.loads(line)
    except ValueError: continue
    msg, now = e.get("eventMessage", ""), None
    if not msg: continue
    now = t(e)
    flags = []
    if m := re.match(r"(fit|slideIn) h=(\S+) -> (\S+)", msg):
        asked.add(round(float(m[3]), 1))
        if m[1] == "slideIn" and "visible=true" in msg and abs(float(m[2]) - float(m[3])) <= 1: flags.append("RESTART")
    elif m := re.match(r"content (\S+) -> (\S+)", msg):
        key = re.findall(r"(?:rows|filter)=(\S+)", msg)
        contents = [c for c in contents if now - c[0] <= 5] + [(now, round(float(m[1]), 1), round(float(m[2]), 1), key)]
        if len(contents) >= 2 and contents[-1][3] != contents[-2][3]:
            pass
        elif len(contents) >= 2 and contents[-1][2] == contents[-2][1] and contents[-1][1] == contents[-2][2]:
            flags.append("FLIP %s <-> %s" % (contents[-1][1], contents[-1][2]))
        elif len(contents) >= 2 and now - contents[-2][0] <= 1:
            d1, d2 = contents[-2][2] - contents[-2][1], contents[-1][2] - contents[-1][1]
            if d1 * d2 < 0 and min(abs(d1), abs(d2)) >= 20: flags.append("BOUNCE %s -> %s -> %s" % (contents[-2][1], contents[-1][1], contents[-1][2]))
    elif m := re.match(r"resized h=(\S+) .* live=(\w+)", msg):
        h, live = round(float(m[1]), 1), m[2] == "true"
        if not live:
            # AppKit rounds a fitted height to whole points.
            if all(abs(h - a) > 1 for a in asked): flags.append("FOREIGN h=%s (asked: %s)" % (h, sorted(asked)[-3:]))
            key = contents[-1][3] if contents else None
            resizes = [r for r in resizes if now - r[0] <= 1 and r[1] == key] + [(now, key)]
            if len(resizes) >= 3: flags.append("BURST %d resizes in 1 s" % len(resizes))
            elif len(resizes) == 2 and now - resizes[0][0] <= 0.1: flags.append("TWICE in %d ms" % round(1000 * (now - resizes[0][0])))
        asked = {h}
    print(e["timestamp"][11:23], msg, *(("<<", " ".join(flags)) if flags else ()), flush=True)
'
