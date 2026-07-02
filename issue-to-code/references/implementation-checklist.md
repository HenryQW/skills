# Implementation checklist

Use this reference when deciding scope, validation, and staging for `issue-to-code`.

## Scope source

- Treat `gh issue view <issue_number> --comments` as the requirements source.
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

## Repository inspection

- Use `rg` and `rg --files` for discovery.
- Prefer existing code paths, tests, helpers, and conventions.
- Avoid new dependencies unless the issue explicitly requires them.
- Do not refactor adjacent code to make the change feel cleaner.
- Add tests only when they directly validate the requested behavior.

## Validation discovery

Prefer the narrowest relevant command discoverable from repository files:

- Package scripts in `package.json`.
- Python tooling in `pyproject.toml`, `tox.ini`, `noxfile.py`, or `pytest.ini`.
- Make targets in `Makefile`.
- Existing CI commands in `.github/workflows/`.
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
