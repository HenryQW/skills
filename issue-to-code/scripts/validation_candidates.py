#!/usr/bin/env python3
"""Suggest local validation commands without running them."""

from __future__ import annotations

import argparse
import json
import shlex
import subprocess
from pathlib import Path


def git(args: list[str]) -> list[str]:
    result = subprocess.run(["git", *args], check=True, text=True, stdout=subprocess.PIPE)
    return [line for line in result.stdout.splitlines() if line]


def status_paths() -> list[str]:
    result = subprocess.run(
        ["git", "status", "--porcelain=v1", "-z"],
        check=True,
        stdout=subprocess.PIPE,
    )
    entries = result.stdout.decode().split("\0")
    paths = []
    index = 0
    while index < len(entries):
        entry = entries[index]
        index += 1
        if not entry:
            continue
        status = entry[:2]
        path = entry[3:]
        if status[0] in ("R", "C") and index < len(entries):
            path = entries[index]
            index += 1
        paths.append(path)
    return paths


def working_tree_files() -> set[str]:
    files = set(git(["diff", "--name-only"]) + git(["diff", "--cached", "--name-only"]))
    for path in status_paths():
        item = Path(path)
        if item.is_dir():
            files.update(str(child) for child in item.rglob("*") if child.is_file())
        else:
            files.add(path)
    return files


def changed_files(base: str | None) -> list[str]:
    files = working_tree_files()
    if base:
        files.update(git(["diff", "--name-only", f"{base}...HEAD"]))
    return sorted(files)


def package_manager(directory: Path) -> str:
    for current in (directory, *directory.parents):
        if (current / "pnpm-lock.yaml").exists():
            return "pnpm"
        if (current / "yarn.lock").exists():
            return "yarn"
        if (current / "bun.lock").exists() or (current / "bun.lockb").exists():
            return "bun"
    return "npm"


def package_jsons(files: list[str]) -> list[Path]:
    paths = set()
    if Path("package.json").exists():
        paths.add(Path("package.json"))
    for name in files:
        path = Path(name)
        start = path if path.is_dir() else path.parent
        for current in (start, *start.parents):
            candidate = current / "package.json"
            if candidate.exists():
                paths.add(candidate)
    return sorted(paths, key=lambda item: len(item.parts), reverse=True)


def package_scripts(files: list[str]) -> list[str]:
    commands = []
    for path in package_jsons(files):
        scripts = json.loads(path.read_text()).get("scripts", {})
        directory = path.parent
        prefix = "" if directory == Path(".") else f"(cd {shlex.quote(str(directory))} && "
        suffix = "" if directory == Path(".") else ")"
        manager = package_manager(directory)
        for name in ("test", "typecheck", "lint", "build"):
            if name in scripts:
                commands.append(f"{prefix}{manager} run {name}{suffix}")
    return commands


def python_commands(files: list[str]) -> list[str]:
    commands = []
    if any(Path(name).exists() for name in ("pyproject.toml", "pytest.ini", "tox.ini")):
        commands.append("python -m pytest")
    tests = [path for path in files if Path(path).name.startswith("test_") and path.endswith(".py")]
    if tests:
        commands.insert(0, "python -m pytest " + " ".join(shlex.quote(path) for path in tests[:5]))
    return commands


def make_commands() -> list[str]:
    return ["make test"] if Path("Makefile").exists() else []


def main() -> int:
    parser = argparse.ArgumentParser(description="Print validation command candidates.")
    parser.add_argument("--base", help="Use branch diff against this base branch")
    args = parser.parse_args()

    files = changed_files(args.base)
    commands = []
    commands.extend(package_scripts(files))
    commands.extend(python_commands(files))
    commands.extend(make_commands())

    seen = set()
    for command in commands:
        if command not in seen:
            seen.add(command)
            print(command)

    if not seen:
        print("No obvious validation command found.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
