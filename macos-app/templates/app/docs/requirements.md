# Requirements

What must be true now.

- **This file:** what. Edit a line in place when a requirement changes; never keep a replaced line.
- **Decision log** (`docs/decisions/log.md`): why, with the options. Append only. A line here may name its D-number.
- **ADRs** (`docs/adr/`): why, for the few choices that are hard to reverse.

Rules:

- Read this file before a UI change. Do not break a line without the user's approval.
- Add or edit the line in the same commit as the change.
- IDs are stable: a new line takes the next free number in its area; a removed line's ID is not used again.
- "(user)" marks a requirement the user asked for or picked.

## GEN: General

- **GEN-1** (user) The app runs on macOS __MIN_MACOS__ or later and builds with Command Line Tools only (ADR 0001).
- **GEN-2** TODO(scaffold): the first product requirement.
