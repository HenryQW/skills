#!/usr/bin/env python3
"""Local Git and GitHub access for issue-workbench CLIs."""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path


class CommandError(RuntimeError):
    def __init__(self, message: str, returncode: int = 1) -> None:
        super().__init__(message)
        self.returncode = returncode


def _command(command: list[str], cwd: str | None = None) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(command, cwd=cwd, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except OSError as exc:
        raise CommandError(str(exc), 127) from exc


def run(command: list[str], *, cwd: str | None = None) -> str:
    result = _command(command, cwd)
    if result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip()
        raise CommandError(detail or f"{command[0]} exited {result.returncode}", result.returncode)
    return result.stdout.strip()


def local_branch_exists(name: str) -> bool:
    result = _command(
        ["git", "show-ref", "--verify", "--quiet", f"refs/heads/{name}"],
    )
    if result.returncode not in {0, 1}:
        raise CommandError(result.stderr.strip() or "git show-ref failed", result.returncode)
    return result.returncode == 0


def remote_branch_exists(name: str) -> bool:
    return bool(run(["git", "ls-remote", "--heads", "origin", name]))


def default_branch() -> str:
    return run(["gh", "repo", "view", "--json", "defaultBranchRef", "--jq", ".defaultBranchRef.name"])


def issue(number: str, fields: str, repo: str | None = None) -> dict[str, object]:
    command = ["gh", "issue", "view", number, "--json", fields]
    if repo:
        command.extend(["--repo", repo])
    try:
        value = json.loads(run(command))
    except json.JSONDecodeError as exc:
        raise CommandError(f"invalid JSON from gh issue view: {exc}") from exc
    if not isinstance(value, dict):
        raise CommandError("gh issue view returned a non-object JSON value")
    return value


def current_branch() -> str:
    return run(["git", "branch", "--show-current"])


def revision(ref: str, *, cwd: str | None = None) -> str:
    return run(["git", "rev-parse", ref], cwd=cwd)


def status_lines() -> list[str]:
    return run(["git", "status", "--short"]).splitlines()


def diff_snapshot(base: str) -> tuple[list[str], str]:
    diff = f"{base}...HEAD"
    files = run(["git", "diff", "--name-only", diff]).splitlines()
    stat = run(["git", "diff", "--stat", diff]).replace("\n", " | ")
    return files, stat


def add_worktree(path: Path, branch: str, base: str) -> None:
    run(["git", "worktree", "add", "-b", branch, os.fspath(path), base])
