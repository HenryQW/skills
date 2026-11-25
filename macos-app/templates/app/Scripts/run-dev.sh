#!/bin/sh
# Runs one dev build at a time on this Mac. Waits for the lock that another run holds, opens the app, holds the lock
# until the app quits, then unregisters it so the Dock and Spotlight do not keep it.
set -eu
exec /usr/bin/lockf -k /tmp/__EXEC_LOWER__-dev.lock /bin/sh -c '
    open -n -W "$1"
    /System/Library/Frameworks/CoreServices.framework/Frameworks/LaunchServices.framework/Support/lsregister -u "$1"
' run-dev "$1"
