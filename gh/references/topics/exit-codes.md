# Exit codes

| Code | Meaning |
|---:|---|
| 0 | A command completes successfully |
| 1 | A command fails for any reason |
| 2 | A command is running but gets cancelled |
| 4 | A command requires authentication |

Commands may define additional exit codes; check that command's details before branching on status.
