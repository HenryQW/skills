# Details

## Description

List installed agent skills across known agent host directories.

By default, scans all supported agent hosts in both project and user scope.
Use `--agent` to scan one host, `--scope` to scan only project or user
scope, or `--dir` to scan a custom skills directory.

Project-scope skills are discovered relative to the current git repository
root. User-scope skills are discovered relative to your home directory.

For more information about output formatting flags, see `gh help formatting`.

## Json Fields

  agentHosts, path, pinned, scope, skillName, sourceURL, version
