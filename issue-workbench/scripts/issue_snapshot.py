#!/usr/bin/env python3
"""Print a compact markdown snapshot of a GitHub issue."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
import tempfile
from pathlib import Path

from repository import GITHUB, GitHubError


def clip(text: str | None, limit: int) -> str:
    text = (text or "").strip()
    if len(text) <= limit:
        return text
    return text[: limit - 20].rstrip() + "\n\n[truncated]"


def snapshot(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Compact a GitHub issue for implementation.")
    parser.add_argument("issue_number")
    parser.add_argument("--body-chars", type=int, default=4000)
    parser.add_argument("--comment-chars", type=int, default=600)
    parser.add_argument("--max-comments", type=int, default=5, help="Print only the last N comments")
    args = parser.parse_args(argv)
    if args.max_comments < 1:
        print("--max-comments must be a positive integer", file=sys.stderr)
        return 2
    if args.body_chars < 80 or args.comment_chars < 80:
        print("--body-chars and --comment-chars must be at least 80", file=sys.stderr)
        return 2

    fields = "number,title,state,url,labels,body,comments"
    try:
        GITHUB.authenticate()
        data = GITHUB.issue_json(args.issue_number, fields)
    except (GitHubError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return getattr(exc, "returncode", 2)
    labels = ", ".join(label.get("name", "") for label in data.get("labels", []) if label.get("name"))

    print(f"# Issue #{data.get('number')}: {str(data.get('title', '')).strip()}")
    print(f"- State: {data.get('state', '')}")
    print(f"- URL: {data.get('url', '')}")
    if labels:
        print(f"- Labels: {labels}")

    print("\n## Body")
    print(clip(str(data.get("body") or ""), args.body_chars) or "[empty]")

    all_comments = data.get("comments") or []
    omitted = max(0, len(all_comments) - args.max_comments)
    comments = all_comments[-args.max_comments :]
    if comments:
        print("\n## Comments")
        if omitted:
            print(f"\n[omitted {omitted} older comment{'s' if omitted != 1 else ''}]")
    for comment in comments:
        author = (comment.get("author") or {}).get("login", "unknown")
        created = comment.get("createdAt", "")
        print(f"\n### {author} {created}")
        print(clip(comment.get("body"), args.comment_chars) or "[empty]")

    return 0


def self_test() -> int:
    with tempfile.TemporaryDirectory() as raw_tmp:
        fake_gh = Path(raw_tmp) / "gh"
        fake_gh.write_text(
            "#!/bin/sh\n"
            "if [ \"$1\" = auth ]; then exit 0; fi\n"
            "if [ \"$1\" = repo ]; then printf '%s\\n' '{\"nameWithOwner\":\"owner/repo\"}'; exit 0; fi\n"
            "if [ \"$3\" = 500 ]; then echo 'fake gh failure' >&2; exit 7; fi\n"
            "printf '%s\\n' '{\"number\":23,\"title\":\"Adapter\",\"state\":\"OPEN\",\"url\":\"https://example.invalid/23\",\"labels\":[{\"name\":\"enhancement\"}],\"body\":\"Body\",\"comments\":[]}'\n",
            encoding="utf-8",
        )
        fake_gh.chmod(0o755)
        env = {**os.environ, "PATH": f"{raw_tmp}{os.pathsep}{os.environ.get('PATH', '')}"}
        success = subprocess.run([sys.executable, __file__, "23"], text=True, capture_output=True, env=env)
        assert success.returncode == 0, success.stderr
        assert "# Issue #23: Adapter" in success.stdout
        failure = subprocess.run([sys.executable, __file__, "500"], text=True, capture_output=True, env=env)
        assert failure.returncode == 7
        assert failure.stderr.strip() == "fake gh failure"
    return 0


def main() -> int:
    if sys.argv[1:] == ["--self-test"]:
        return self_test()
    return snapshot(sys.argv[1:])


if __name__ == "__main__":
    raise SystemExit(main())
