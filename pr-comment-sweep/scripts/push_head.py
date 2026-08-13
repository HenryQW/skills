#!/usr/bin/env python3
"""Push clean local HEAD to PR head branch through matching GitHub remote."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Sequence
from urllib.parse import urlparse

from fetch_feedback import SweepError, require_clean_head, resolve_metadata


def run(command: Sequence[str]) -> str:
    result = subprocess.run(command, text=True, capture_output=True)
    if result.returncode:
        detail = (result.stderr or result.stdout).strip()
        raise SweepError(f"command failed: {' '.join(command)}\n{detail}")
    return result.stdout.strip()


def load_metadata(path: str) -> dict[str, Any]:
    try:
        data = json.loads(Path(path).read_text())["pull_request"]
    except (OSError, json.JSONDecodeError, KeyError, TypeError) as error:
        raise SweepError(f"invalid feedback snapshot {path}: {error}") from error
    if not isinstance(data, dict):
        raise SweepError(f"invalid feedback snapshot {path}")
    return data


def normalize_github_remote(url: str) -> str | None:
    scp = re.fullmatch(r"(?:[^@]+@)?github\.com:([^/]+/[^/]+?)(?:\.git)?", url)
    if scp:
        return scp.group(1).lower()
    parsed = urlparse(url)
    if (parsed.hostname or "").lower() != "github.com":
        return None
    path = parsed.path.strip("/")
    if path.endswith(".git"):
        path = path[:-4]
    return path.lower() if path.count("/") == 1 else None


def matching_remote(repository: str) -> str:
    target = repository.lower()
    matches: list[str] = []
    for remote in run(("git", "remote")).splitlines():
        urls = run(("git", "remote", "get-url", "--push", "--all", remote)).splitlines()
        if any(normalize_github_remote(url) == target for url in urls):
            matches.append(remote)
    if len(matches) != 1:
        raise SweepError(
            f"expected one push remote for {repository}, found {len(matches)}: {matches}"
        )
    return matches[0]


def push_head(snapshot: dict[str, Any]) -> None:
    local_head = require_clean_head()
    current = resolve_metadata(snapshot["url"], None)
    if current["head_ref_oid"] != snapshot["head_ref_oid"]:
        raise SweepError(
            "PR head changed since feedback fetch: "
            f"{snapshot['head_ref_oid']} -> {current['head_ref_oid']}"
        )
    if local_head == current["head_ref_oid"]:
        raise SweepError("local HEAD already matches PR head; no push needed")
    remote = matching_remote(current["head_repository"])
    run(("git", "push", remote, f"HEAD:{current['head_ref_name']}"))
    pushed = resolve_metadata(current["url"], None)
    if pushed["head_ref_oid"] != local_head:
        raise SweepError(
            f"push did not update PR head to local HEAD: {pushed['head_ref_oid']} != {local_head}"
        )
    print(f"pushed={local_head} remote={remote} branch={current['head_ref_name']}")


def self_test() -> None:
    for url in (
        "git@github.com:Owner/Repo.git",
        "ssh://git@github.com/Owner/Repo.git",
        "https://github.com/Owner/Repo.git",
    ):
        assert normalize_github_remote(url) == "owner/repo"
    assert normalize_github_remote("https://example.com/o/r.git") is None
    assert normalize_github_remote("https://github.com/o/r/extra.git") is None


def main(argv: list[str]) -> int:
    if argv == ["--self-test"]:
        self_test()
        return 0
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--snapshot", required=True, help="output from fetch_feedback.py")
    args = parser.parse_args(argv)
    try:
        push_head(load_metadata(args.snapshot))
    except SweepError as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
