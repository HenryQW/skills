#!/usr/bin/env python3
"""Authenticated GitHub CLI transport and canonical reference resolution."""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Sequence


Runner = Callable[..., subprocess.CompletedProcess[bytes]]
REPOSITORY = re.compile(r"[^/\s]+/[^/\s]+")


class GitHubError(RuntimeError):
    def __init__(self, message: str, returncode: int = 1) -> None:
        super().__init__(message)
        self.returncode = returncode


@dataclass(frozen=True)
class GitHubResult:
    command: tuple[str, ...]
    returncode: int
    stdout: bytes
    stderr: bytes

    @property
    def text(self) -> str:
        return self.stdout.decode(errors="replace")

    @property
    def error(self) -> str:
        return self.stderr.decode(errors="replace")

    @property
    def message(self) -> str:
        return (self.error or self.text).strip()

    def json(self) -> Any:
        try:
            return json.loads(self.text)
        except json.JSONDecodeError as exc:
            raise GitHubError(f"invalid JSON from {' '.join(self.command)}: {exc}") from exc


@dataclass(frozen=True)
class GitHubRef:
    repository: str
    number: int

    @property
    def owner(self) -> str:
        return self.repository.split("/", 1)[0]

    @property
    def name(self) -> str:
        return self.repository.split("/", 1)[1]


def _default_runner(command: list[str], **kwargs: Any) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(command, capture_output=True, **kwargs)


class GitHub:
    def __init__(self, runner: Runner = _default_runner) -> None:
        self.runner = runner

    def execute(
        self,
        args: Sequence[str],
        *,
        cwd: str | Path | None = None,
        input: str | bytes | None = None,
        check: bool = True,
    ) -> GitHubResult:
        command = ["gh", *args]
        payload = input.encode() if isinstance(input, str) else input
        try:
            completed = self.runner(
                command,
                cwd=os.fspath(cwd) if cwd is not None else None,
                input=payload,
            )
        except OSError as exc:
            raise GitHubError(f"unable to execute gh: {exc}", 127) from exc
        result = GitHubResult(
            tuple(command),
            completed.returncode,
            completed.stdout or b"",
            completed.stderr or b"",
        )
        if check and result.returncode:
            raise GitHubError(result.message or f"gh exited {result.returncode}", result.returncode)
        return result

    def text(self, args: Sequence[str], **kwargs: Any) -> str:
        return self.execute(args, **kwargs).text

    def bytes(self, args: Sequence[str], **kwargs: Any) -> bytes:
        return self.execute(args, **kwargs).stdout

    def json(self, args: Sequence[str], **kwargs: Any) -> Any:
        return self.execute(args, **kwargs).json()

    def authenticate(self, *, cwd: str | Path | None = None) -> None:
        try:
            self.execute(["auth", "status"], cwd=cwd)
        except GitHubError as exc:
            raise GitHubError(str(exc) or "gh is not authenticated", exc.returncode) from exc

    def resolve_repository(self, repository: str | None = None, *, cwd: str | Path | None = None) -> str:
        if repository is not None:
            if not REPOSITORY.fullmatch(repository):
                raise ValueError("repository must be OWNER/REPO")
            return repository
        data = self.json(["repo", "view", "--json", "nameWithOwner"], cwd=cwd)
        value = data.get("nameWithOwner") if isinstance(data, dict) else None
        if not isinstance(value, str) or not REPOSITORY.fullmatch(value):
            raise GitHubError("gh repo view returned no canonical repository")
        return value

    def resolve_issue(
        self,
        reference: str | int,
        repository: str | None = None,
        *,
        cwd: str | Path | None = None,
    ) -> GitHubRef:
        parsed = self._url_reference(str(reference), "issues")
        if parsed:
            return parsed
        value = str(reference).removeprefix("#")
        if not re.fullmatch(r"[1-9][0-9]*", value):
            raise ValueError("issue must be a number or GitHub issue URL")
        return GitHubRef(self.resolve_repository(repository, cwd=cwd), int(value))

    def resolve_pr(
        self,
        reference: str | int | None = None,
        repository: str | None = None,
        *,
        cwd: str | Path | None = None,
    ) -> GitHubRef:
        if reference is not None:
            parsed = self._url_reference(str(reference), "pull")
            if parsed:
                return parsed
            value = str(reference).removeprefix("#")
            if not re.fullmatch(r"[1-9][0-9]*", value):
                raise ValueError("pull request must be a number or GitHub pull request URL")
            return GitHubRef(self.resolve_repository(repository, cwd=cwd), int(value))

        args = ["pr", "view"]
        if repository:
            args.extend(["--repo", self.resolve_repository(repository)])
        args.extend(["--json", "number,url"])
        data = self.json(args, cwd=cwd)
        url = data.get("url") if isinstance(data, dict) else None
        parsed = self._url_reference(str(url or ""), "pull")
        if not parsed:
            raise GitHubError("gh pr view returned no canonical pull request")
        return parsed

    def issue_json(
        self,
        reference: str | int,
        fields: str,
        repository: str | None = None,
        *,
        cwd: str | Path | None = None,
    ) -> dict[str, Any]:
        resolved = self.resolve_issue(reference, repository, cwd=cwd)
        value = self.json(
            ["issue", "view", str(resolved.number), "--repo", resolved.repository, "--json", fields],
            cwd=cwd,
        )
        if not isinstance(value, dict):
            raise GitHubError("gh issue view returned a non-object JSON value")
        return value

    def default_branch(self, repository: str | None = None, *, cwd: str | Path | None = None) -> str:
        resolved = self.resolve_repository(repository, cwd=cwd)
        value = self.json(["repo", "view", resolved, "--json", "defaultBranchRef"], cwd=cwd)
        branch = value.get("defaultBranchRef", {}).get("name") if isinstance(value, dict) else None
        if not isinstance(branch, str) or not branch:
            raise GitHubError("gh repo view returned no default branch")
        return branch

    def graphql(self, query: str, variables: dict[str, str | int | None]) -> dict[str, Any]:
        args = ["api", "graphql", "-F", "query=@-"]
        for key, value in variables.items():
            if value is not None:
                args.extend(["-F", f"{key}={value}"])
        payload = self.json(args, input=query)
        if not isinstance(payload, dict):
            raise GitHubError("gh api graphql returned a non-object JSON value")
        return payload

    @staticmethod
    def _url_reference(value: str, kind: str) -> GitHubRef | None:
        match = re.fullmatch(
            rf"https://github\.com/([^/\s]+/[^/\s]+)/{kind}/([1-9][0-9]*)/?",
            value,
        )
        return GitHubRef(match.group(1), int(match.group(2))) if match else None


def self_test() -> None:
    calls: list[tuple[list[str], bytes | None]] = []

    def fake(command: list[str], **kwargs: Any) -> subprocess.CompletedProcess[bytes]:
        calls.append((command, kwargs.get("input")))
        args = command[1:]
        if args == ["auth", "status"]:
            return subprocess.CompletedProcess(command, 0, b"ok\n", b"")
        if args == ["echo"]:
            return subprocess.CompletedProcess(command, 0, b"hello\n", b"")
        if args == ["raw"]:
            return subprocess.CompletedProcess(command, 0, b"\xffdata", b"")
        if args == ["good-json"]:
            return subprocess.CompletedProcess(command, 0, b'{"ok":true}', b"")
        if args == ["bad-json"]:
            return subprocess.CompletedProcess(command, 0, b"not-json", b"")
        if args == ["fail"]:
            return subprocess.CompletedProcess(command, 7, b"", b"failure\n")
        if args[:3] == ["repo", "view", "--json"]:
            return subprocess.CompletedProcess(command, 0, b'{"nameWithOwner":"owner/repo"}', b"")
        if args[:3] == ["repo", "view", "owner/repo"]:
            return subprocess.CompletedProcess(command, 0, b'{"defaultBranchRef":{"name":"main"}}', b"")
        if args[:2] == ["pr", "view"]:
            return subprocess.CompletedProcess(command, 0, b'{"number":9,"url":"https://github.com/owner/repo/pull/9"}', b"")
        if args[:2] == ["api", "graphql"]:
            return subprocess.CompletedProcess(command, 0, b'{"data":{}}', b"")
        raise AssertionError(args)

    github = GitHub(fake)
    github.authenticate()
    assert github.text(["echo"]) == "hello\n"
    assert github.bytes(["raw"]) == b"\xffdata"
    assert github.json(["good-json"]) == {"ok": True}
    assert github.resolve_repository("explicit/repo") == "explicit/repo"
    assert github.resolve_repository() == "owner/repo"
    assert github.default_branch() == "main"
    assert github.resolve_issue("12", "explicit/repo") == GitHubRef("explicit/repo", 12)
    assert github.resolve_issue("https://github.com/o/r/issues/13") == GitHubRef("o/r", 13)
    assert github.resolve_pr("14", "explicit/repo") == GitHubRef("explicit/repo", 14)
    assert github.resolve_pr("https://github.com/o/r/pull/15") == GitHubRef("o/r", 15)
    assert github.resolve_pr() == GitHubRef("owner/repo", 9)
    assert github.graphql("query Q { viewer { login } }", {"number": 1, "cursor": None}) == {"data": {}}
    assert calls[-1][1] == b"query Q { viewer { login } }"
    for args, expected in ((["fail"], "failure"), (["bad-json"], "invalid JSON")):
        try:
            github.json(args)
        except GitHubError as exc:
            assert expected in str(exc)
        else:
            raise AssertionError(f"expected {expected}")

    def unauthenticated(command: list[str], **_kwargs: Any) -> subprocess.CompletedProcess[bytes]:
        return subprocess.CompletedProcess(command, 1, b"", b"not logged in")

    try:
        GitHub(unauthenticated).authenticate()
    except GitHubError as exc:
        assert "not logged in" in str(exc)
    else:
        raise AssertionError("authentication failure accepted")


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Resolve authenticated GitHub references.")
    parser.add_argument("--self-test", action="store_true")
    subparsers = parser.add_subparsers(dest="command")
    repository = subparsers.add_parser("repository")
    repository.add_argument("--repo")
    repository.add_argument("--default-branch", action="store_true")
    issue = subparsers.add_parser("issue")
    issue.add_argument("reference")
    issue.add_argument("--repo")
    pr = subparsers.add_parser("pr")
    pr.add_argument("reference", nargs="?")
    pr.add_argument("--repo")
    subparsers.add_parser("auth")
    args = parser.parse_args(argv)
    if args.self_test:
        self_test()
        return 0
    if not args.command:
        parser.print_help(sys.stderr)
        return 2
    github = GitHub()
    try:
        github.authenticate()
        if args.command == "auth":
            return 0
        if args.command == "repository":
            print(github.default_branch(args.repo) if args.default_branch else github.resolve_repository(args.repo))
        elif args.command == "issue":
            resolved = github.resolve_issue(args.reference, args.repo)
            print(f"{resolved.repository}#{resolved.number}")
        else:
            resolved = github.resolve_pr(args.reference, args.repo)
            print(f"{resolved.repository}#{resolved.number}")
        return 0
    except (GitHubError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return getattr(exc, "returncode", 2)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
