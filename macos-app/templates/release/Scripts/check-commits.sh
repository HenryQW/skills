#!/bin/sh
# Fails if a commit subject in <range> does not follow Conventional Commits (AGENTS.md): `type(scope): summary`, with
# a known type, an optional scope and `!`, and a lower-case summary with no full stop. Merges are left out.
# Usage: bash Scripts/check-commits.sh <range>, for example v0.1.1..HEAD.
set -eu
subjects=$(git log --no-merges --format='%h %s' "${1:?commit range required}" --)
printf '%s\n' "$subjects" | awk '
    NF == 0 { next }
    { count++ }
    !/^[0-9a-f]+ (feat|fix|docs|refactor|perf|test|build|ci|chore|revert)(\([a-z0-9._\/-]+\))?!?: [a-z0-9](.*[^.])?$/ {
        print "Invalid Conventional Commit: " $0; bad = 1
    }
    END { if (bad) exit 1; print count+0 " commit subjects follow Conventional Commits." }
'
