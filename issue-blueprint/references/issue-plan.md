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
      "blocked_by": [],
      "blocks": ["tail"],
      "parallelism": "Root blocker; do this first."
    },
    {
      "id": "tail",
      "title": "v4: final verification",
      "role": "final_check",
      "purpose": "Final pass.",
      "context": ["No major architecture work belongs here."],
      "acceptance": ["All checks pass."],
      "blocked_by": ["foundation"],
      "blocks": [],
      "parallelism": "Final tail."
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
- `dropped_findings` is optional, but required when repo-surveyor or review findings were excluded before publish. Record the reason so the parent graph explains why duplicates were not sliced.
- Exactly one issue must use `"role": "final_check"`; it must be blocked by every non-final child and block nothing.
- Keep bodies short enough to scan, but include enough context for an AFK agent.
- The renderer rejects invalid IDs, unknown dependencies, cycles, wave-order errors, and mismatched `blocks` / `blocked_by`.
