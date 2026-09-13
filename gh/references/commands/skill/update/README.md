# gh skill update

Checks installed skills for available updates by comparing the local tree SHA (from `SKILL.md` frontmatter) against the remote repository.

**Usage:** `gh skill update [<skill>...] [flags]`

## Options
  --all          Update all skills without prompting
  --dir string   Scan a custom directory for installed skills
  --dry-run      Report available updates without modifying files
  --force        Re-download even if already up to date
  --unpin        Clear pinned version and include pinned skills in update

## More
- [Examples](examples.md)
- [Details](details.md)
