#!/usr/bin/env python3
"""Local Git and GitHub access for issue-workbench CLIs."""

from __future__ import annotations

import json
import os
import re
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


def normalize_slug(raw: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", raw.lower()).strip("-")
    return re.sub(r"-{2,}", "-", slug)


def branch_name(issue_number: str, branch_slug: str | None = None) -> str:
    if not re.fullmatch(r"[1-9][0-9]*", issue_number):
        raise ValueError("issue_number must be a positive integer")
    if not branch_slug:
        return f"issue-{issue_number}"
    slug = normalize_slug(branch_slug)
    if not slug:
        raise ValueError("branch_slug must contain at least one letter or digit")
    return f"issue-{issue_number}-{slug}"


def integration_branch_name_from_title(title: str) -> str:
    slug = normalize_slug(title)
    if not slug:
        raise ValueError("parent issue title must contain at least one letter or digit")
    return f"feat/{slug}"


def integration_branch_name(parent_issue: str, repo: str | None = None) -> str:
    match = re.fullmatch(r"(?:(?:https://github\.com/[^/\s]+/[^/\s]+/issues/)|#)?([1-9][0-9]*)/?", parent_issue.strip())
    if not match:
        raise ValueError("parent_issue must be a positive integer, #number, or GitHub issue URL")
    title = issue(match.group(1), "title", repo).get("title", "")
    return integration_branch_name_from_title(str(title))


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


def create_issue_branch(
    issue_number: str,
    *,
    base_branch: str | None = None,
    branch_slug: str | None = None,
    worktree_path: str | None = None,
    integration_branch: str | None = None,
) -> list[str]:
    name = branch_name(issue_number, branch_slug)
    if local_branch_exists(name):
        raise RuntimeError(f"local branch already exists: {name}")

    if worktree_path:
        if not integration_branch:
            raise RuntimeError("--integration-branch is required with --worktree-path")
        path = Path(worktree_path)
        if path.exists():
            raise RuntimeError(f"worktree path already exists: {path}")
        base_commit = revision(integration_branch)
        add_worktree(path, name, integration_branch)
        if revision("HEAD", cwd=os.fspath(path)) != base_commit:
            raise RuntimeError(f"child branch was not created from {integration_branch}")
        return [f"branch={name}", f"worktree={path}"]

    if integration_branch:
        raise RuntimeError("--integration-branch requires --worktree-path")
    if remote_branch_exists(name):
        raise RuntimeError(f"origin branch already exists: {name}")
    run(["git", "fetch", "origin"])
    base = base_branch or default_branch()
    run(["git", "checkout", "-b", name, f"origin/{base}"])
    return [f"branch={name}"]
