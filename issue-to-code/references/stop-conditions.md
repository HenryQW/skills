# Stop conditions

Stop instead of guessing when any condition applies:

- The working tree has pre-existing changes and the user did not ask to continue with them.
- The issue is not an actionable implementation request.
- The issue requires a product decision or behavior not stated in the issue.
- The smallest implementation would modify forbidden paths without explicit issue text requiring it.
- The diff contains unrelated changes, broad formatting, generated output, or adjacent cleanup.
- Validation failure points outside the requested implementation and requires a separate decision.
- Commit scope would mix unrelated logical units.

Do not push, open a PR, or run Greptile in this skill.
