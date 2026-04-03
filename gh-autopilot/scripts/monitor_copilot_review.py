#!/usr/bin/env python3
"""
Monitor a pull request until a new Copilot review exists or timeout is reached.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

NO_COMMENTS_RE = re.compile(r"generated\s+no\s+comments", re.IGNORECASE)
COMMENTS_RE = re.compile(r"generated\s+(\d+)\s+comments?", re.IGNORECASE)
FILES_RE = re.compile(
    r"reviewed\s+(\d+)\s+out\s+of\s+(\d+)\s+changed\s+files", re.IGNORECASE
)
COPILOT_LOGIN_HINTS = ("copilot-pull-request-reviewer", "copilot")

REVIEWS_QUERY = """\
query($owner: String!, $repo: String!, $number: Int!) {
  repository(owner: $owner, name: $repo) {
    pullRequest(number: $number) {
      number
      url
      reviews(last: 100) {
        nodes {
          id
          state
          body
          submittedAt
          author { login }
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


def fetch_reviews(cwd: Path, pr: dict[str, Any]) -> list[dict[str, Any]]:
    payload = run_json(
        [
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
        ],
        cwd=cwd,
        stdin=REVIEWS_QUERY,
    )
    errors = payload.get("errors") or []
    if errors:
        raise RuntimeError(f"graphql errors: {json.dumps(errors, indent=2)}")
    pr_data = payload["data"]["repository"]["pullRequest"]
    reviews = pr_data["reviews"]["nodes"] or []
    return [r for r in reviews if isinstance(r, dict)]


def is_copilot_login(login: str | None) -> bool:
    if not login:
        return False
    lowered = login.lower()
    return any(hint in lowered for hint in COPILOT_LOGIN_HINTS)


def latest_copilot_review(reviews: list[dict[str, Any]]) -> dict[str, Any] | None:
    copilot_reviews = [
        review
        for review in reviews
        if is_copilot_login((review.get("author") or {}).get("login"))
    ]
    if not copilot_reviews:
        return None
    # GraphQL returns `reviews(last: 100)` in chronological order; keep a stable
    # fallback using submittedAt to avoid accidental reprocessing.
    return max(
        copilot_reviews,
        key=lambda r: (r.get("submittedAt") or "", r.get("id") or ""),
    )


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


def write_output(result: dict[str, Any], output: Path | None) -> None:
    rendered = json.dumps(result, indent=2, sort_keys=True)
    if output:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(rendered + "\n", encoding="utf-8")
    print(rendered)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Wait for a new Copilot PR review with fixed polling behavior."
    )
    parser.add_argument("--repo", default=".", help="Local repository path.")
    parser.add_argument("--pr", default=None, help="PR number or URL.")
    parser.add_argument(
        "--initial-sleep-seconds",
        type=int,
        default=300,
        help="First wait before polling.",
    )
    parser.add_argument(
        "--poll-interval-seconds",
        type=int,
        default=45,
        help="Polling interval after initial sleep.",
    )
    parser.add_argument(
        "--cycle-max-wait-seconds",
        dest="max_wait_seconds",
        type=int,
        default=2400,
        help="Maximum per-cycle wait before declaring timeout.",
    )
    parser.add_argument(
        "--exclude-review-id",
        default=None,
        help="Ignore this review id and wait for a newer Copilot review.",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Optional output path for monitor JSON.",
    )
    return parser.parse_args()


def validate_timing(args: argparse.Namespace) -> None:
    if args.initial_sleep_seconds < 0:
        raise ValueError("--initial-sleep-seconds must be >= 0")
    if args.poll_interval_seconds <= 0:
        raise ValueError("--poll-interval-seconds must be > 0")
    if args.max_wait_seconds <= 0:
        raise ValueError("--cycle-max-wait-seconds must be > 0")


def monitor(args: argparse.Namespace) -> tuple[int, dict[str, Any]]:
    cwd = Path(args.repo).resolve()
    ensure_gh_auth(cwd)
    pr = resolve_pr(cwd, args.pr)

    start = time.monotonic()
    deadline = start + args.max_wait_seconds
    poll_count = 0
    exceeded_ten_minutes = False

    initial_sleep = min(args.initial_sleep_seconds, max(0, int(deadline - start)))
    if initial_sleep > 0:
        time.sleep(initial_sleep)

    while True:
        poll_count += 1
        now = time.monotonic()
        elapsed_seconds = int(now - start)
        exceeded_ten_minutes = exceeded_ten_minutes or elapsed_seconds >= 600

        review = latest_copilot_review(fetch_reviews(cwd, pr))

        if review and review.get("id") != args.exclude_review_id:
            body = review.get("body") or ""
            parsed = parse_summary(body)
            status = "reviewed_unknown"
            if parsed["signals_no_comments"]:
                status = "no_comments"
            elif parsed["generated_comments"] is not None:
                status = "no_comments" if parsed["generated_comments"] == 0 else "has_comments"

            result = {
                "status": status,
                "pr": pr,
                "timing": {
                    "initial_sleep_seconds": args.initial_sleep_seconds,
                    "poll_interval_seconds": args.poll_interval_seconds,
                    "max_wait_seconds": args.max_wait_seconds,
                    "elapsed_seconds": elapsed_seconds,
                    "poll_count": poll_count,
                    "exceeded_ten_minutes": exceeded_ten_minutes,
                },
                "copilot_review": {
                    "id": review.get("id"),
                    "state": review.get("state"),
                    "submitted_at": review.get("submittedAt"),
                    "author": (review.get("author") or {}).get("login"),
                    "body": body,
                },
                "parsed_summary": parsed,
            }
            return 0, result

        if now >= deadline:
            timeout = {
                "status": "timeout",
                "reason": "no_new_copilot_review_before_deadline",
                "pr": pr,
                "timing": {
                    "initial_sleep_seconds": args.initial_sleep_seconds,
                    "poll_interval_seconds": args.poll_interval_seconds,
                    "max_wait_seconds": args.max_wait_seconds,
                    "elapsed_seconds": int(now - start),
                    "poll_count": poll_count,
                    "exceeded_ten_minutes": exceeded_ten_minutes,
                },
                "excluded_review_id": args.exclude_review_id,
            }
            return 3, timeout

        remaining_seconds = max(1, int(deadline - now))
        sleep_seconds = min(args.poll_interval_seconds, remaining_seconds)
        time.sleep(sleep_seconds)


def main() -> int:
    try:
        args = parse_args()
        validate_timing(args)
        code, payload = monitor(args)
        output_path = Path(args.output).resolve() if args.output else None
        write_output(payload, output_path)
        return code
    except Exception as exc:  # pragma: no cover - defensive CLI boundary
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
