#!/usr/bin/env python3
"""
Export normalized Copilot review feedback for autonomous processing.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

NO_COMMENTS_RE = re.compile(r"generated\s+no\s+comments", re.IGNORECASE)
COMMENTS_RE = re.compile(r"generated\s+(\d+)\s+comments?", re.IGNORECASE)
FILES_RE = re.compile(
    r"reviewed\s+(\d+)\s+out\s+of\s+(\d+)\s+changed\s+files", re.IGNORECASE
)
COPILOT_LOGIN_HINTS = ("copilot-pull-request-reviewer", "copilot")

GRAPHQL_QUERY = """\
query(
  $owner: String!,
  $repo: String!,
  $number: Int!,
  $reviewsCursor: String,
  $threadsCursor: String
) {
  repository(owner: $owner, name: $repo) {
    pullRequest(number: $number) {
      number
      url
      title
      reviews(first: 100, after: $reviewsCursor) {
        pageInfo { hasNextPage endCursor }
        nodes {
          id
          state
          body
          submittedAt
          author { login }
        }
      }
      reviewThreads(first: 100, after: $threadsCursor) {
        pageInfo { hasNextPage endCursor }
        nodes {
          id
          isResolved
          isOutdated
          path
          line
          startLine
          originalLine
          originalStartLine
          diffSide
          startDiffSide
          comments(first: 100) {
            nodes {
              id
              body
              createdAt
              updatedAt
              url
              author { login }
            }
          }
        }
      }
    }
  }
}
"""


def run(cmd: list[str], *, cwd: Path, stdin: str | None = None) -> str:
    proc = subprocess.run(
        cmd,
        input=stdin,
        cwd=str(cwd),
        text=True,
        capture_output=True,
        check=False,
    )
    if proc.returncode != 0:
        raise RuntimeError(
            f"command failed ({proc.returncode}): {' '.join(cmd)}\n{proc.stderr.strip()}"
        )
    return proc.stdout


def run_json(cmd: list[str], *, cwd: Path, stdin: str | None = None) -> dict[str, Any]:
    raw = run(cmd, cwd=cwd, stdin=stdin)
    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"failed to decode json output: {exc}\nraw:\n{raw}") from exc


def ensure_gh_auth(cwd: Path) -> None:
    run(["gh", "auth", "status"], cwd=cwd)


def resolve_pr(cwd: Path, pr_ref: str | None) -> dict[str, Any]:
    cmd = ["gh", "pr", "view"]
    if pr_ref:
        cmd.append(pr_ref)
    cmd.extend(["--json", "number,url,headRepositoryOwner,headRepository"])
    payload = run_json(cmd, cwd=cwd)
    return {
        "number": int(payload["number"]),
        "url": payload["url"],
        "owner": payload["headRepositoryOwner"]["login"],
        "repo": payload["headRepository"]["name"],
    }


def is_copilot_login(login: str | None) -> bool:
    if not login:
        return False
    lowered = login.lower()
    return any(hint in lowered for hint in COPILOT_LOGIN_HINTS)


def parse_summary(body: str) -> dict[str, Any]:
    files_match = FILES_RE.search(body)
    comments_match = COMMENTS_RE.search(body)
    no_comments = bool(NO_COMMENTS_RE.search(body))
    return {
        "files_reviewed": int(files_match.group(1)) if files_match else None,
        "files_total": int(files_match.group(2)) if files_match else None,
        "generated_comments": int(comments_match.group(1)) if comments_match else None,
        "signals_no_comments": no_comments,
    }


def fetch_pr_feedback(cwd: Path, pr: dict[str, Any]) -> dict[str, Any]:
    reviews_cursor: str | None = None
    threads_cursor: str | None = None
    all_reviews: list[dict[str, Any]] = []
    all_threads: list[dict[str, Any]] = []
    pr_meta: dict[str, Any] | None = None

    while True:
        cmd = [
            "gh",
            "api",
            "graphql",
            "-F",
            "query=@-",
            "-F",
            f"owner={pr['owner']}",
            "-F",
            f"repo={pr['repo']}",
            "-F",
            f"number={pr['number']}",
        ]
        if reviews_cursor:
            cmd.extend(["-F", f"reviewsCursor={reviews_cursor}"])
        if threads_cursor:
            cmd.extend(["-F", f"threadsCursor={threads_cursor}"])

        payload = run_json(cmd, cwd=cwd, stdin=GRAPHQL_QUERY)
        errors = payload.get("errors") or []
        if errors:
            raise RuntimeError(f"graphql errors: {json.dumps(errors, indent=2)}")

        pr_data = payload["data"]["repository"]["pullRequest"]
        if pr_meta is None:
            pr_meta = {
                "number": int(pr_data["number"]),
                "url": pr_data["url"],
                "title": pr_data["title"],
                "owner": pr["owner"],
                "repo": pr["repo"],
            }

        reviews_page = pr_data["reviews"]
        threads_page = pr_data["reviewThreads"]

        all_reviews.extend(reviews_page.get("nodes") or [])
        all_threads.extend(threads_page.get("nodes") or [])

        reviews_cursor = (
            reviews_page["pageInfo"]["endCursor"]
            if reviews_page["pageInfo"]["hasNextPage"]
            else None
        )
        threads_cursor = (
            threads_page["pageInfo"]["endCursor"]
            if threads_page["pageInfo"]["hasNextPage"]
            else None
        )

        if not reviews_cursor and not threads_cursor:
            break

    if pr_meta is None:
        raise RuntimeError("unable to resolve pull request metadata")

    return {"pull_request": pr_meta, "reviews": all_reviews, "threads": all_threads}


def latest_copilot_review(reviews: list[dict[str, Any]]) -> dict[str, Any] | None:
    copilot_reviews = [
        review
        for review in reviews
        if is_copilot_login((review.get("author") or {}).get("login"))
    ]
    if not copilot_reviews:
        return None
    return max(
        copilot_reviews,
        key=lambda r: (r.get("submittedAt") or "", r.get("id") or ""),
    )


def normalize_threads(threads: list[dict[str, Any]]) -> list[dict[str, Any]]:
    normalized: list[dict[str, Any]] = []
    index = 0
    for thread in threads:
        comments = (thread.get("comments") or {}).get("nodes") or []
        if not comments:
            continue
        if not any(is_copilot_login((c.get("author") or {}).get("login")) for c in comments):
            continue

        index += 1
        normalized_comments = []
        for comment in comments:
            normalized_comments.append(
                {
                    "id": comment.get("id"),
                    "author": (comment.get("author") or {}).get("login"),
                    "body": comment.get("body") or "",
                    "created_at": comment.get("createdAt"),
                    "updated_at": comment.get("updatedAt"),
                    "url": comment.get("url"),
                }
            )

        is_resolved = bool(thread.get("isResolved"))
        is_outdated = bool(thread.get("isOutdated"))
        normalized.append(
            {
                "thread_number": index,
                "thread_id": thread.get("id"),
                "path": thread.get("path"),
                "line": thread.get("line"),
                "start_line": thread.get("startLine"),
                "original_line": thread.get("originalLine"),
                "original_start_line": thread.get("originalStartLine"),
                "diff_side": thread.get("diffSide"),
                "start_diff_side": thread.get("startDiffSide"),
                "is_resolved": is_resolved,
                "is_outdated": is_outdated,
                "eligible_for_addressing": not is_resolved and not is_outdated,
                "comments": normalized_comments,
            }
        )
    return normalized


def detect_status(review: dict[str, Any] | None, threads: list[dict[str, Any]]) -> tuple[str, dict[str, Any]]:
    if review is None:
        return "no_review", {"files_reviewed": None, "files_total": None, "generated_comments": None, "signals_no_comments": False}

    parsed = parse_summary(review.get("body") or "")
    if parsed["signals_no_comments"]:
        return "no_comments", parsed
    if parsed["generated_comments"] is not None:
        if parsed["generated_comments"] == 0:
            return "no_comments", parsed
        return "has_comments", parsed

    active_threads = [thread for thread in threads if thread["eligible_for_addressing"]]
    if active_threads:
        return "has_comments", parsed
    return "reviewed_unknown", parsed


def render_markdown(payload: dict[str, Any]) -> str:
    pr = payload["pull_request"]
    review = payload.get("copilot_review")
    parsed = payload["parsed_summary"]
    status = payload["status"]
    threads = payload["copilot_threads"]
    lines: list[str] = []

    lines.append("# Copilot Feedback Context")
    lines.append("")
    lines.append(f"- PR: #{pr['number']} ({pr['url']})")
    lines.append(f"- Repository: {pr['owner']}/{pr['repo']}")
    lines.append(f"- Status: {status}")
    lines.append(
        f"- Summary parse: files={parsed['files_reviewed']}/{parsed['files_total']}, "
        f"generated_comments={parsed['generated_comments']}, "
        f"signals_no_comments={parsed['signals_no_comments']}"
    )
    lines.append("")

    if review:
        lines.append("## Copilot Review")
        lines.append("")
        lines.append(f"- Review id: {review.get('id')}")
        lines.append(f"- Submitted: {review.get('submitted_at')}")
        lines.append(f"- State: {review.get('state')}")
        lines.append("")
        lines.append("Body:")
        lines.append("")
        for raw_line in (review.get("body") or "").splitlines():
            lines.append(f"> {raw_line}")
        if not (review.get("body") or "").strip():
            lines.append("> (empty)")
        lines.append("")
    else:
        lines.append("## Copilot Review")
        lines.append("")
        lines.append("No Copilot review found for this PR.")
        lines.append("")

    lines.append("## Threads")
    lines.append("")
    if not threads:
        lines.append("No Copilot-authored review threads found.")
        lines.append("")
        return "\n".join(lines).rstrip() + "\n"

    for thread in threads:
        lines.append(
            f"### Thread {thread['thread_number']} "
            f"(eligible={thread['eligible_for_addressing']})"
        )
        lines.append("")
        lines.append(f"- Thread id: {thread['thread_id']}")
        lines.append(f"- Path: {thread['path']}")
        lines.append(f"- Line: {thread['line']}")
        lines.append(f"- Start line: {thread['start_line']}")
        lines.append(f"- Resolved: {thread['is_resolved']}")
        lines.append(f"- Outdated: {thread['is_outdated']}")
        lines.append("")
        lines.append("Comments:")
        lines.append("")
        for idx, comment in enumerate(thread["comments"], start=1):
            lines.append(
                f"{idx}. @{comment['author']} "
                f"({comment['created_at']}) id={comment['id']}"
            )
            for raw_line in comment["body"].splitlines():
                lines.append(f"   {raw_line}")
            if not comment["body"].strip():
                lines.append("   (empty)")
            lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Export Copilot review details into normalized JSON + Markdown."
    )
    parser.add_argument("--repo", default=".", help="Local repository path.")
    parser.add_argument("--pr", default=None, help="PR number or URL.")
    parser.add_argument(
        "--output-json",
        default=".context/gh-autopilot/copilot-review-export.json",
        help="Output path for normalized JSON payload.",
    )
    parser.add_argument(
        "--output-md",
        default=".context/gh-autopilot/copilot-review-export.md",
        help="Output path for markdown context payload.",
    )
    return parser.parse_args()


def main() -> int:
    try:
        args = parse_args()
        cwd = Path(args.repo).resolve()
        ensure_gh_auth(cwd)
        pr = resolve_pr(cwd, args.pr)
        raw = fetch_pr_feedback(cwd, pr)

        review = latest_copilot_review(raw["reviews"])
        threads = normalize_threads(raw["threads"])
        status, parsed_summary = detect_status(review, threads)

        payload = {
            "status": status,
            "pull_request": raw["pull_request"],
            "copilot_review": (
                {
                    "id": review.get("id"),
                    "state": review.get("state"),
                    "submitted_at": review.get("submittedAt"),
                    "author": (review.get("author") or {}).get("login"),
                    "body": review.get("body") or "",
                }
                if review
                else None
            ),
            "parsed_summary": parsed_summary,
            "counts": {
                "copilot_threads_total": len(threads),
                "copilot_threads_eligible": sum(
                    1 for thread in threads if thread["eligible_for_addressing"]
                ),
            },
            "copilot_threads": threads,
        }

        json_path = Path(args.output_json).resolve()
        md_path = Path(args.output_md).resolve()
        json_path.parent.mkdir(parents=True, exist_ok=True)
        md_path.parent.mkdir(parents=True, exist_ok=True)
        json_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        md_path.write_text(render_markdown(payload), encoding="utf-8")

        print(json.dumps({"status": payload["status"], "output_json": str(json_path), "output_md": str(md_path)}))
        return 0
    except Exception as exc:  # pragma: no cover - defensive CLI boundary
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
