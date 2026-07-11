# Issue Plan JSON

Use this compact JSON shape, then render it with `scripts/render_issue_plan.py`.

```json
{
  "tracker": {
    "title": "v4 implementation tracker",
    "goal": "One paragraph outcome.",
    "constraints": ["First-principles rule."],
    "non_goals": ["Scope explicitly skipped."],
    "definition_of_done": ["Final verifiable condition."]
  },
  "dropped_findings": [
    {"finding": "Existing route/session cleanup draft.", "reason": "Duplicate of #123; excluded before publish."}
  ],
  "issues": [
    {
      "id": "foundation",
      "title": "v4: build the foundation",
      "purpose": "One sentence purpose.",
      "context": ["Why this issue exists."],
      "acceptance": ["A concrete checkbox."],
      "testing": {
        "seam": "Public interface or behavior boundary under test.",
        "existing_tests": "tests/example.test.ts or none found",
        "validation": "npm test -- example.test.ts",
        "do_not_test": "Implementation details or private helpers."
      },
      "blocked_by": [],
      "blocks": ["tail"],
      "parallelism": "Owns the foundation seam; no same-wave issues."
    },
    {
      "id": "tail",
      "title": "v4: final verification",
      "role": "final_check",
      "purpose": "Final pass.",
      "context": ["No major architecture work belongs here."],
      "acceptance": ["All checks pass."],
      "testing": {
        "seam": "Final integrated workflow.",
        "existing_tests": "All child tests above.",
        "validation": "npm test",
        "do_not_test": "Child-owned implementation details."
      },
      "blocked_by": ["foundation"],
      "blocks": [],
      "parallelism": "Runs only after every implementation child; no same-wave issues."
    }
  ],
  "waves": [
    {"name": "Wave 0", "items": ["foundation"], "notes": "Root blocker."},
    {"name": "Wave 1", "items": ["tail"], "notes": "Final tail."}
  ]
}
```

Rules:
- `id` is stable and lowercase. It becomes the filename slug and numbers-map key.
- `blocked_by` and `blocks` use issue IDs, not GitHub numbers.
- `tracker` creates the implementation tracker issue. Do not create a child issue for the implementation tracker.
- Use `context` to justify an unusually small or large issue boundary.
- `parallelism` must explain why the issue is safe in its wave and identify expected overlap in files, interfaces, or shared state with same-wave issues.
- `testing` is required for every implementation child. It captures the public seam, existing similar tests, smallest validation command, and what not to test. Use `seam: none` only with a concrete alternative validation path.
- `dropped_findings` is optional, but required when repo-surveyor or review findings were excluded before publish. Record the reason so the parent graph explains why duplicates were not sliced.
- Exactly one issue must use `"role": "final_check"`; it must be blocked by every non-final child and block nothing.
- Keep bodies short enough to scan, but include enough context for an AFK agent.
- Every issue must appear in exactly one explicit wave.
- The renderer rejects missing required fields, invalid IDs, unknown dependencies, cycles, duplicate or invalid wave membership, and mismatched `blocks` / `blocked_by`.
