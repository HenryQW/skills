# Details

## Description

Checks installed skills for available updates by comparing the local
tree SHA (from `SKILL.md` frontmatter) against the remote repository.

Scans all known agent host directories (including Copilot, Claude, Cursor,
Gemini, Antigravity, Grok, and others) in both project and user scope automatically.

Without arguments, checks all installed skills. With skill names,
checks only those specific skills.

Pinned skills (installed with `--pin`) are skipped with a notice.
Use `--unpin` to clear the pinned version and include those skills
in the update.

Skills without GitHub metadata (e.g. installed manually or by another
tool) are prompted for their source repository in interactive mode.
With `--all` or in non-interactive mode, they are skipped with a notice.
The update re-downloads the skill with metadata injected, so future
updates work automatically.

With `--force`, re-downloads skills even when the remote version matches
the local tree SHA. This overwrites locally modified skill files with
their original content, but does not remove extra files added locally.

In interactive mode, shows which skills have updates and asks for
confirmation before proceeding. With `--all`, updates without prompting.
With `--dry-run`, reports available updates without modifying any files.
