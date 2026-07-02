# Implementation checklist

Use this reference when deciding scope, validation, and staging for `issue-to-code`.

## Scope source

- Treat `scripts/issue_snapshot.py <issue_number>` as the compact requirements source.
- If truncation or omitted comments hide context needed to decide scope, rerun it with larger limits before implementing.
- Extract explicit requirements, acceptance criteria, constraints, named files, named modules, and named behavior.
- Stop when the issue lacks an actionable implementation request.
- Stop when a product decision is required.
- For partial ambiguity, choose the smallest implementation that satisfies explicit issue text.

## Forbidden changes

Do not modify these unless the issue explicitly requires it:

- Secrets or credential files.
- Environment files.
- Generated files.
- Lockfiles.
- `.context/`.
- `.agents/`.
- Infrastructure files.

If one appears in `git diff`, either justify it from the issue text or revert your own change before committing.

Run `scripts/diff_guard.py` before staging.

If the issue explicitly requires a blocked path, verify that requirement in the issue text, then rerun:

```bash
python3 <skill_dir>/scripts/diff_guard.py --allow <path>
```

## Repository inspection

- Use `rg` and `rg --files` for discovery.
- Prefer existing code paths, tests, helpers, and conventions.
- Avoid new dependencies unless the issue explicitly requires them.
- Do not refactor adjacent code to make the change feel cleaner.
- Add tests only when they directly validate the requested behavior.

## Validation discovery

Prefer the narrowest relevant command discoverable by `scripts/validation_candidates.py`.

- Package scripts in `package.json`.
- Python tooling in `pyproject.toml`, `tox.ini`, `noxfile.py`, or `pytest.ini`.
- Make targets in `Makefile`.
- Nearby test files that match the changed module.

If no command is obvious, continue and keep the commit focused.

## Diff review before staging

Run:

```bash
git status --short
git diff --stat
git diff
```

Check that every changed line traces to the issue.

Stage explicit paths only:

```bash
git add <file1> <file2>
```

Do not use `git add .` unless the full diff has been inspected and every changed file is intentional.

## Stop conditions

Stop instead of guessing when any condition applies:

- The working tree has pre-existing changes and the user did not ask to continue with them.
- The issue is not an actionable implementation request.
- The issue requires a product decision or behavior not stated in the issue.
- The smallest implementation would modify forbidden paths without explicit issue text requiring it.
- The diff contains unrelated changes, broad formatting, generated output, or adjacent cleanup.
- Validation failure points outside the requested implementation and requires a separate decision.
- Commit scope would mix unrelated logical units.

Do not push, open a PR, or run Greptile in this skill.
