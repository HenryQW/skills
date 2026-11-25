#!/bin/sh
# Prints the release notes for the commits from <previous tag> to <tag>, grouped by Conventional Commits type:
# Breaking changes, Features, Fixes, Performance, Documentation, then Other. A scope shows in bold before the summary.
# The release commit (chore: release x.y.z) and merges are left out.
# Usage: bash Scripts/release-notes.sh <previous tag> <tag> <owner/repo>
set -eu
subjects=$(git log --no-merges --reverse --format='%s' "${1:?previous revision required}..${2:?end revision required}" --)
printf '%s\n' "$subjects" | awk -v prev="$1" -v tag="$2" -v repo="$3" '
NF == 0 || /^chore: release / { next }
{
    group = "Other"; line = $0
    if (match($0, /^[a-z]+(\([^)]*\))?!?: /)) {
        head = substr($0, 1, RLENGTH - 2); line = substr($0, RLENGTH + 1)
        type = head; sub(/[(!].*/, "", type)
        scope = ""
        if (match(head, /\([^)]*\)/)) scope = substr(head, RSTART + 1, RLENGTH - 2)
        if (scope != "") line = "**" scope ":** " line
        if (head ~ /!$/) group = "Breaking changes"
        else if (type == "feat") group = "Features"
        else if (type == "fix") group = "Fixes"
        else if (type == "perf") group = "Performance"
        else if (type == "docs") group = "Documentation"
    }
    items[group] = items[group] "- " line "\n"
}
END {
    n = split("Breaking changes,Features,Fixes,Performance,Documentation,Other", order, ",")
    for (i = 1; i <= n; i++) if (order[i] in items) printf "## %s\n\n%s\n", order[i], items[order[i]]
    printf "All changes: https://github.com/%s/compare/%s...%s\n", repo, prev, tag
}'
