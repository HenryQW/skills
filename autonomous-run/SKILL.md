---
name: autonomous-run
description: Run a bounded development task while the user is away. Use when the user requests an unattended or overnight run.
---

# Autonomous Run

## Before the user leaves

Use the agreed milestone, acceptance checks, and permissions. Ask one batch of questions only when a missing answer changes the work. Default to the current milestone and local work. Obtain explicit permission before publishing or changing shared state.

Keep builds and tests in user-writable directories. If installation requires administrator access, leave the verified artifact and record the attended installation step. Never add an unattended privilege grant.

For visual checks, establish whether the host can capture the app window and control the app. On macOS, screen recording and accessibility are separate permissions. If permission requires a restart, defer the affected check and continue other work.

## While the user is away

1. Write the milestone, acceptance checks, and remaining work in the project's progress file. Update it after each completed stage.
2. Choose reversible options within the agreed scope. Record consequential choices, the supporting evidence, and the cost of a wrong choice. Send a difficult decision to an independent reviewer when one is available.
3. Give independent writers separate worktrees. When delegation is unavailable, work sequentially and review the combined change against the acceptance checks.
4. Use primary sources to resolve uncertain facts. Keep the evidence with the decision that uses it.
5. Run the relevant checks through the normal entry points. Fix failures and exercise the affected paths again. Record any checks the environment prevents.
6. When work requires a new permission, payment, credential, or owner decision, record it under `Needs user`. Continue independent work.

## Window checks

Capture only the app's window. On macOS, identify its window number through `CGWindowListCopyWindowInfo`, then run `screencapture -x -o -l <windowNumber> <scratch>/shot.png`. Verify that the intended app is frontmost before sending input. Remove temporary captures after review.

## Handoff

Keep secrets out of files, commits, logs, and reports. Preserve the user's files and existing repository rules. Return one report with the milestone result, important decisions, exact checks, remaining risks, and actions that need the user. Link local artifacts by path when file delivery is unavailable.
