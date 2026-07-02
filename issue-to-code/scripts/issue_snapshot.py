#!/usr/bin/env python3
"""Print a compact markdown snapshot of a GitHub issue."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys


def clip(text: str | None, limit: int) -> str:
    text = (text or "").strip()
    if len(text) <= limit:
        return text
    return text[: limit - 20].rstrip() + "\n\n[truncated]"


def main() -> int:
    parser = argparse.ArgumentParser(description="Compact a GitHub issue for implementation.")
    parser.add_argument("issue_number")
    parser.add_argument("--body-chars", type=int, default=6000)
    parser.add_argument("--comment-chars", type=int, default=1200)
    parser.add_argument("--max-comments", type=int, default=8, help="Print only the last N comments")
    args = parser.parse_args()
    if args.max_comments < 1:
        print("--max-comments must be a positive integer", file=sys.stderr)
        return 2
    if args.body_chars < 80 or args.comment_chars < 80:
        print("--body-chars and --comment-chars must be at least 80", file=sys.stderr)
        return 2

    fields = "number,title,state,url,labels,body,comments"
    try:
        result = subprocess.run(
            ["gh", "issue", "view", args.issue_number, "--json", fields],
            check=True,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
    except subprocess.CalledProcessError as exc:
        print(exc.stderr.strip() or str(exc), file=sys.stderr)
        return exc.returncode

    issue = json.loads(result.stdout)
    labels = ", ".join(label.get("name", "") for label in issue.get("labels", []) if label.get("name"))

    print(f"# Issue #{issue.get('number')}: {issue.get('title', '').strip()}")
    print(f"- State: {issue.get('state', '')}")
    print(f"- URL: {issue.get('url', '')}")
    if labels:
        print(f"- Labels: {labels}")

    print("\n## Body")
    print(clip(issue.get("body"), args.body_chars) or "[empty]")

    all_comments = issue.get("comments") or []
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


if __name__ == "__main__":
    raise SystemExit(main())
