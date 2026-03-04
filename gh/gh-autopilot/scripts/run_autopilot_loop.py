#!/usr/bin/env python3
"""
Standalone GH Autopilot engine with explicit state transitions.

The script owns control-plane actions for Copilot review loops:
- waiting for a new Copilot review
- exporting normalized cycle artifacts
- managing lifecycle state and event logs
- re-requesting Copilot reviewer after a batch is addressed
"""

from __future__ import annotations

import argparse
import json
import re
import shlex
import subprocess
import sys
import time
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

COPILOT_REVIEWER_LOGIN = "copilot-pull-request-reviewer"
COPILOT_LOGIN_HINTS = (COPILOT_REVIEWER_LOGIN, "copilot")

NO_COMMENTS_RE = re.compile(r"generated\s+no(?:\s+new)?\s+comments", re.IGNORECASE)
COMMENTS_RE = re.compile(r"generated\s+(\d+)\s+comments?", re.IGNORECASE)
FILES_RE = re.compile(
    r"reviewed\s+(\d+)\s+out\s+of\s+(\d+)\s+changed\s+files", re.IGNORECASE
)

STATE_VERSION = 2
CONTEXT_FORMAT_VERSION = 1

STATUS_INITIALIZED = "initialized"
STATUS_WAITING = "waiting_for_review"
STATUS_AWAITING_ADDRESS = "awaiting_address"
STATUS_AWAITING_TRIAGE = "awaiting_triage"
STATUS_REREQUESTED = "rerequested"
STATUS_TIMEOUT = "timeout"
STATUS_COMPLETED_NO_COMMENTS = "completed_no_comments"
STATUS_BLOCKED_UNADDRESSED = "blocked_unaddressed_comments"
TERMINAL_STATUSES = {STATUS_TIMEOUT, STATUS_COMPLETED_NO_COMMENTS}

TIMEOUT_REASON_CYCLE_MAX_WAIT_REACHED = "cycle_max_wait_reached"
TIMEOUT_REASON_STAGE2_MAX_WAIT_REACHED = "stage2_max_wait_reached"

EVENT_BEGIN_CYCLE_WAIT = "begin_cycle_wait"
EVENT_CYCLE_TIMEOUT = "cycle_timeout"
EVENT_CYCLE_NO_COMMENTS = "cycle_no_comments"
EVENT_CYCLE_NEEDS_ADDRESS = "cycle_needs_address"
EVENT_CYCLE_NEEDS_TRIAGE = "cycle_needs_triage"
EVENT_STAGE2_RETRY_AFTER_CYCLE_TIMEOUT = "stage2_retry_after_cycle_timeout"
EVENT_STAGE2_MAX_WAIT_REACHED = "stage2_max_wait_reached"
EVENT_FINALIZE_WITH_REVIEWER_REQUEST = "finalize_with_reviewer_request"
EVENT_FINALIZE_WITHOUT_REVIEWER_REQUEST = "finalize_without_reviewer_request"

STATE_TRANSITIONS: dict[tuple[str, str], str] = {
    (STATUS_INITIALIZED, EVENT_BEGIN_CYCLE_WAIT): STATUS_WAITING,
    (STATUS_REREQUESTED, EVENT_BEGIN_CYCLE_WAIT): STATUS_WAITING,
    (STATUS_WAITING, EVENT_BEGIN_CYCLE_WAIT): STATUS_WAITING,
    (STATUS_WAITING, EVENT_CYCLE_TIMEOUT): STATUS_TIMEOUT,
    (STATUS_WAITING, EVENT_CYCLE_NO_COMMENTS): STATUS_COMPLETED_NO_COMMENTS,
    (STATUS_WAITING, EVENT_CYCLE_NEEDS_ADDRESS): STATUS_AWAITING_ADDRESS,
    (STATUS_WAITING, EVENT_CYCLE_NEEDS_TRIAGE): STATUS_AWAITING_TRIAGE,
    (STATUS_TIMEOUT, EVENT_STAGE2_RETRY_AFTER_CYCLE_TIMEOUT): STATUS_INITIALIZED,
    (STATUS_INITIALIZED, EVENT_STAGE2_MAX_WAIT_REACHED): STATUS_TIMEOUT,
    (STATUS_WAITING, EVENT_STAGE2_MAX_WAIT_REACHED): STATUS_TIMEOUT,
    (STATUS_REREQUESTED, EVENT_STAGE2_MAX_WAIT_REACHED): STATUS_TIMEOUT,
    (STATUS_TIMEOUT, EVENT_STAGE2_MAX_WAIT_REACHED): STATUS_TIMEOUT,
    (STATUS_AWAITING_ADDRESS, EVENT_FINALIZE_WITH_REVIEWER_REQUEST): STATUS_REREQUESTED,
    (STATUS_AWAITING_ADDRESS, EVENT_FINALIZE_WITHOUT_REVIEWER_REQUEST): STATUS_INITIALIZED,
    (STATUS_AWAITING_TRIAGE, EVENT_FINALIZE_WITH_REVIEWER_REQUEST): STATUS_REREQUESTED,
    (STATUS_AWAITING_TRIAGE, EVENT_FINALIZE_WITHOUT_REVIEWER_REQUEST): STATUS_INITIALIZED,
}

DEFAULT_OUTPUT_DIR = ".context/gh-autopilot"
DEFAULT_CONTEXT_FILENAME = "context.md"
DEFAULT_CYCLE_FILENAME = "cycle.json"
DEFAULT_COMMENT_STATUS_HISTORY_FILENAME = "comment-status-history.json"
DEFAULT_STAGE2_MAX_WAIT_SECONDS = 43200
EVENT_SCHEMA_VERSION = 1
PHASE_FINALIZED = "finalized"
EXIT_BLOCKED_UNADDRESSED = 11
EXIT_STAGE2_MAX_WAIT_REACHED = 12

SIMULATION_START_STATUSES = sorted(
    {status for status, _ in STATE_TRANSITIONS.keys()} | set(STATE_TRANSITIONS.values())
)
SIMULATION_EVENTS = sorted({event for _, event in STATE_TRANSITIONS.keys()})

REVIEWS_QUERY = """\
query(
  $owner: String!,
  $repo: String!,
  $number: Int!,
  $cursor: String
) {
  repository(owner: $owner, name: $repo) {
    pullRequest(number: $number) {
      number
      url
      title
      reviews(first: 100, after: $cursor) {
        pageInfo { hasNextPage endCursor }
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

THREADS_QUERY = """\
query(
  $owner: String!,
  $repo: String!,
  $number: Int!,
  $cursor: String
) {
  repository(owner: $owner, name: $repo) {
    pullRequest(number: $number) {
      reviewThreads(first: 100, after: $cursor) {
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
              pullRequestReview {
                id
                submittedAt
              }
            }
          }
        }
      }
    }
  }
}
"""


def now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def transition_status(current_status: str, event: str) -> str:
    next_status = STATE_TRANSITIONS.get((current_status, event))
    if next_status is None:
        raise ValueError(
            f"invalid state transition: status={current_status}, event={event}"
        )
    return next_status


def normalize_event_type(event_type: str) -> str:
    if not isinstance(event_type, str):
        raise ValueError("event_type must be a string")
    normalized = re.sub(r"[^a-z0-9]+", "_", event_type.strip().lower()).strip("_")
    if not normalized:
        raise ValueError("event_type must contain at least one alphanumeric character")
    return normalized


def parse_iso(value: str | None) -> datetime | None:
    if not value:
        return None
    normalized = value.replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(normalized).astimezone(UTC)
    except ValueError:
        return None


def is_copilot_login(login: str | None) -> bool:
    if not login:
        return False
    lowered = login.lower()
    if lowered == COPILOT_REVIEWER_LOGIN:
        return True
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


def render_json(data: dict[str, Any]) -> str:
    return json.dumps(data, indent=2, sort_keys=True)


class CommandError(RuntimeError):
    pass


@dataclass
class GhPrRef:
    number: int
    url: str
    owner: str
    repo: str
    title: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "number": self.number,
            "url": self.url,
            "owner": self.owner,
            "repo": self.repo,
            "title": self.title,
        }


@dataclass(frozen=True)
class ChecklistTask:
    label: str
    done: bool = False
    command: str | None = None

    def render(self) -> str:
        checkbox = "[x]" if self.done else "[ ]"
        if self.command:
            return f"{checkbox} {self.label}: `{self.command}`"
        return f"{checkbox} {self.label}"


class GhClient:
    def __init__(self, repo_path: Path):
        self.repo_path = repo_path

    def run(self, cmd: list[str], *, stdin: str | None = None) -> str:
        proc = subprocess.run(
            cmd,
            input=stdin,
            cwd=str(self.repo_path),
            text=True,
            capture_output=True,
            check=False,
        )
        if proc.returncode != 0:
            raise CommandError(
                f"command failed ({proc.returncode}): {' '.join(cmd)}\n{proc.stderr.strip()}"
            )
        return proc.stdout

    def run_json(self, cmd: list[str], *, stdin: str | None = None) -> dict[str, Any]:
        raw = self.run(cmd, stdin=stdin)
        try:
            return json.loads(raw)
        except json.JSONDecodeError as exc:
            raise CommandError(
                f"failed to decode JSON output: {exc}\nraw:\n{raw}"
            ) from exc

    def ensure_auth(self) -> None:
        self.run(["gh", "auth", "status"])

    def resolve_pr(self, pr_ref: str | None) -> GhPrRef:
        cmd = ["gh", "pr", "view"]
        if pr_ref:
            cmd.append(pr_ref)
        cmd.extend(
            [
                "--json",
                "number,url,title,headRepositoryOwner,headRepository",
            ]
        )
        payload = self.run_json(cmd)
        return GhPrRef(
            number=int(payload["number"]),
            url=payload["url"],
            title=payload.get("title"),
            owner=payload["headRepositoryOwner"]["login"],
            repo=payload["headRepository"]["name"],
        )

    def graphql(self, query: str, fields: dict[str, str | int]) -> dict[str, Any]:
        cmd = ["gh", "api", "graphql", "-F", "query=@-"]
        for key, value in fields.items():
            cmd.extend(["-F", f"{key}={value}"])
        return self.run_json(cmd, stdin=query)

    def re_request_copilot(self, pr_number: int) -> None:
        remove_cmd = [
            "gh",
            "pr",
            "edit",
            str(pr_number),
            "--remove-reviewer",
            COPILOT_REVIEWER_LOGIN,
        ]
        try:
            self.run(remove_cmd)
        except CommandError:
            # Continue if reviewer is absent.
            pass

        self.run(
            [
                "gh",
                "pr",
                "edit",
                str(pr_number),
                "--add-reviewer",
                COPILOT_REVIEWER_LOGIN,
            ]
        )


class AutopilotStateStore:
    def __init__(self, state_file: Path, events_file: Path):
        self.state_file = state_file
        self.events_file = events_file

    def load(self) -> dict[str, Any]:
        if not self.state_file.exists():
            raise FileNotFoundError(
                f"state file not found: {self.state_file}. Run `init` first."
            )
        raw = self.state_file.read_text(encoding="utf-8")
        state = json.loads(raw)
        if state.get("version") != STATE_VERSION:
            raise ValueError(
                f"unsupported state version: {state.get('version')} (expected {STATE_VERSION})"
            )
        state.setdefault("last_timeout_reason", None)
        state.setdefault("last_wait", None)
        return state

    def save(self, state: dict[str, Any]) -> None:
        state["updated_at"] = now_iso()
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        self.state_file.write_text(render_json(state) + "\n", encoding="utf-8")

    def append_event(self, event_type: str, data: dict[str, Any]) -> None:
        if not isinstance(data, dict):
            raise ValueError("event payload must be a JSON object")
        event = {
            "schema_version": EVENT_SCHEMA_VERSION,
            "timestamp": now_iso(),
            "event_type": normalize_event_type(event_type),
            "payload": data,
        }
        self.events_file.parent.mkdir(parents=True, exist_ok=True)
        with self.events_file.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(event, sort_keys=True) + "\n")


def fetch_all_reviews(client: GhClient, pr: GhPrRef) -> list[dict[str, Any]]:
    cursor: str | None = None
    reviews: list[dict[str, Any]] = []
    while True:
        fields: dict[str, str | int] = {
            "owner": pr.owner,
            "repo": pr.repo,
            "number": pr.number,
        }
        if cursor:
            fields["cursor"] = cursor
        payload = client.graphql(REVIEWS_QUERY, fields)
        errors = payload.get("errors") or []
        if errors:
            raise CommandError(f"graphql errors: {render_json({'errors': errors})}")
        pr_payload = payload["data"]["repository"]["pullRequest"]
        page = pr_payload["reviews"]
        reviews.extend(page.get("nodes") or [])
        if page["pageInfo"]["hasNextPage"]:
            cursor = page["pageInfo"]["endCursor"]
        else:
            break
    return reviews


def latest_copilot_review(
    reviews: list[dict[str, Any]], exclude_review_id: str | None = None
) -> dict[str, Any] | None:
    candidates = []
    for review in reviews:
        login = (review.get("author") or {}).get("login")
        if not is_copilot_login(login):
            continue
        if exclude_review_id and review.get("id") == exclude_review_id:
            continue
        candidates.append(review)
    if not candidates:
        return None
    return max(
        candidates, key=lambda r: (r.get("submittedAt") or "", r.get("id") or "")
    )


def fetch_all_threads(client: GhClient, pr: GhPrRef) -> list[dict[str, Any]]:
    cursor: str | None = None
    threads: list[dict[str, Any]] = []
    while True:
        fields: dict[str, str | int] = {
            "owner": pr.owner,
            "repo": pr.repo,
            "number": pr.number,
        }
        if cursor:
            fields["cursor"] = cursor
        payload = client.graphql(THREADS_QUERY, fields)
        errors = payload.get("errors") or []
        if errors:
            raise CommandError(f"graphql errors: {render_json({'errors': errors})}")
        pr_payload = payload["data"]["repository"]["pullRequest"]
        page = pr_payload["reviewThreads"]
        threads.extend(page.get("nodes") or [])
        if page["pageInfo"]["hasNextPage"]:
            cursor = page["pageInfo"]["endCursor"]
        else:
            break
    return threads


def normalize_threads(
    threads: list[dict[str, Any]],
    *,
    review_id: str | None,
) -> list[dict[str, Any]]:
    normalized: list[dict[str, Any]] = []
    thread_number = 0

    for thread in threads:
        comments = (thread.get("comments") or {}).get("nodes") or []
        if not comments:
            continue

        copilot_comments = []
        for comment in comments:
            author = (comment.get("author") or {}).get("login")
            if not is_copilot_login(author):
                continue
            comment_review = comment.get("pullRequestReview")
            comment_review_id: str | None = None
            if isinstance(comment_review, dict):
                raw_review_id = comment_review.get("id")
                if isinstance(raw_review_id, str) and raw_review_id:
                    comment_review_id = raw_review_id
            if review_id and comment_review_id != review_id:
                continue
            copilot_comments.append(comment)

        if not copilot_comments:
            continue

        thread_number += 1
        serialized_comments = []
        for comment in copilot_comments:
            serialized_comments.append(
                {
                    "id": comment.get("id"),
                    "author": (comment.get("author") or {}).get("login"),
                    "body": comment.get("body") or "",
                    "created_at": comment.get("createdAt"),
                    "updated_at": comment.get("updatedAt"),
                    "url": comment.get("url"),
                    "review_id": (
                        (comment.get("pullRequestReview") or {}).get("id")
                        if isinstance(comment.get("pullRequestReview"), dict)
                        else None
                    ),
                }
            )

        is_resolved = bool(thread.get("isResolved"))
        is_outdated = bool(thread.get("isOutdated"))
        normalized.append(
            {
                "thread_number": thread_number,
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
                "comments": serialized_comments,
            }
        )

    return normalized


def detect_cycle_status(
    review: dict[str, Any], normalized_threads: list[dict[str, Any]]
) -> tuple[str, dict[str, Any]]:
    summary = parse_summary(review.get("body") or "")
    if summary["signals_no_comments"]:
        return STATUS_COMPLETED_NO_COMMENTS, summary
    generated = summary["generated_comments"]
    if generated is not None and generated == 0:
        return STATUS_COMPLETED_NO_COMMENTS, summary
    if generated is not None and generated > 0:
        return STATUS_AWAITING_ADDRESS, summary
    if not normalized_threads:
        # No Copilot thread comments were captured for this review cycle.
        # Treat this as terminal no-comments to avoid unnecessary Stage 3
        # finalization/re-request churn.
        return STATUS_COMPLETED_NO_COMMENTS, summary

    eligible_threads = [t for t in normalized_threads if t["eligible_for_addressing"]]
    if eligible_threads:
        return STATUS_AWAITING_ADDRESS, summary
    return STATUS_AWAITING_TRIAGE, summary


def review_submitted_at(review: dict[str, Any]) -> str | None:
    normalized = review.get("submitted_at")
    if isinstance(normalized, str) and normalized:
        return normalized
    graphql = review.get("submittedAt")
    if isinstance(graphql, str) and graphql:
        return graphql
    return None


def review_author_login(review: dict[str, Any]) -> str | None:
    author = review.get("author")
    if isinstance(author, str):
        return author or None
    if isinstance(author, dict):
        login = author.get("login")
        if isinstance(login, str) and login:
            return login
    return None


def write_cycle_artifact(
    output_dir: Path,
    *,
    cycle: int,
    pr: GhPrRef,
    review: dict[str, Any],
    status: str,
    summary: dict[str, Any],
    threads: list[dict[str, Any]],
) -> dict[str, str]:
    output_dir.mkdir(parents=True, exist_ok=True)
    cycle_json = default_cycle_file(output_dir)

    payload = {
        "version": 1,
        "status": status,
        "cycle": cycle,
        "pull_request": pr.as_dict(),
        "copilot_review": {
            "id": review.get("id"),
            "state": review.get("state"),
            "submitted_at": review_submitted_at(review),
            "author": review_author_login(review),
            "body": review.get("body") or "",
        },
        "parsed_summary": summary,
        "counts": {
            "copilot_threads_total": len(threads),
            "copilot_threads_eligible": sum(
                1 for thread in threads if thread["eligible_for_addressing"]
            ),
            "copilot_comments_total": sum(len(thread["comments"]) for thread in threads),
        },
        "copilot_threads": threads,
        # Stage 3 worker writes this section after processing the batch.
        "addressing": None,
    }

    cycle_json.write_text(render_json(payload) + "\n", encoding="utf-8")
    return {"cycle_json": str(cycle_json)}


def validate_monitor_args(
    initial_sleep_seconds: int,
    poll_interval_seconds: int,
    max_wait_seconds: int,
) -> None:
    if initial_sleep_seconds < 0:
        raise ValueError("--initial-sleep-seconds must be >= 0")
    if poll_interval_seconds <= 0:
        raise ValueError("--poll-interval-seconds must be > 0")
    if max_wait_seconds <= 0:
        raise ValueError("--cycle-max-wait-seconds must be > 0")


def wait_for_new_review(
    client: GhClient,
    *,
    pr: GhPrRef,
    exclude_review_id: str | None,
    initial_sleep_seconds: int,
    poll_interval_seconds: int,
    max_wait_seconds: int,
) -> tuple[str, dict[str, Any]]:
    start = time.monotonic()
    deadline = start + max_wait_seconds
    poll_count = 0

    initial_sleep = min(initial_sleep_seconds, max(0, int(deadline - start)))
    if initial_sleep > 0:
        time.sleep(initial_sleep)

    while True:
        poll_count += 1
        now = time.monotonic()
        elapsed_seconds = int(now - start)

        reviews = fetch_all_reviews(client, pr)
        review = latest_copilot_review(reviews, exclude_review_id=exclude_review_id)
        if review:
            result = {
                "status": "review_found",
                "timing": {
                    "initial_sleep_seconds": initial_sleep_seconds,
                    "poll_interval_seconds": poll_interval_seconds,
                    "max_wait_seconds": max_wait_seconds,
                    "elapsed_seconds": elapsed_seconds,
                    "poll_count": poll_count,
                    "exceeded_ten_minutes": elapsed_seconds >= 600,
                },
                "copilot_review": {
                    "id": review.get("id"),
                    "state": review.get("state"),
                    "submitted_at": review.get("submittedAt"),
                    "author": (review.get("author") or {}).get("login"),
                    "body": review.get("body") or "",
                },
            }
            return "review_found", result

        if now >= deadline:
            timeout = {
                "status": "timeout",
                "reason": "no_new_copilot_review_before_deadline",
                "timing": {
                    "initial_sleep_seconds": initial_sleep_seconds,
                    "poll_interval_seconds": poll_interval_seconds,
                    "max_wait_seconds": max_wait_seconds,
                    "elapsed_seconds": elapsed_seconds,
                    "poll_count": poll_count,
                    "exceeded_ten_minutes": elapsed_seconds >= 600,
                },
                "excluded_review_id": exclude_review_id,
            }
            return "timeout", timeout

        remaining = max(1, int(deadline - now))
        time.sleep(min(poll_interval_seconds, remaining))


def default_state_file(output_dir: Path) -> Path:
    return output_dir / "state.json"


def default_events_file(output_dir: Path) -> Path:
    return output_dir / "events.jsonl"


def default_monitor_file(output_dir: Path) -> Path:
    return output_dir / "monitor.json"


def default_context_file(output_dir: Path) -> Path:
    return output_dir / DEFAULT_CONTEXT_FILENAME


def default_cycle_file(output_dir: Path) -> Path:
    return output_dir / DEFAULT_CYCLE_FILENAME


def default_comment_status_history_file(output_dir: Path) -> Path:
    return output_dir / DEFAULT_COMMENT_STATUS_HISTORY_FILENAME


def shell_join(parts: list[str]) -> str:
    return " ".join(shlex.quote(part) for part in parts)


def build_run_cycle_command(
    output_dir: Path, pr_number: int, timing: dict[str, Any]
) -> str:
    return shell_join(
        [
            "python",
            "skills/gh-autopilot/scripts/run_autopilot_loop.py",
            "--repo",
            ".",
            "--output-dir",
            str(output_dir),
            "--pr",
            str(pr_number),
            "run-cycle",
            "--initial-sleep-seconds",
            str(timing["initial_sleep_seconds"]),
            "--poll-interval-seconds",
            str(timing["poll_interval_seconds"]),
            "--cycle-max-wait-seconds",
            str(timing["max_wait_seconds"]),
        ]
    )


def build_run_stage2_loop_command(
    output_dir: Path,
    pr_number: int,
    timing: dict[str, Any],
    *,
    stage2_max_wait_seconds: int = DEFAULT_STAGE2_MAX_WAIT_SECONDS,
) -> str:
    return shell_join(
        [
            "python",
            "skills/gh-autopilot/scripts/run_autopilot_loop.py",
            "--repo",
            ".",
            "--output-dir",
            str(output_dir),
            "--pr",
            str(pr_number),
            "run-stage2-loop",
            "--initial-sleep-seconds",
            str(timing["initial_sleep_seconds"]),
            "--poll-interval-seconds",
            str(timing["poll_interval_seconds"]),
            "--cycle-max-wait-seconds",
            str(timing["max_wait_seconds"]),
            "--stage2-max-wait-seconds",
            str(stage2_max_wait_seconds),
        ]
    )


def build_finalize_cycle_command(output_dir: Path, pr_number: int) -> str:
    return shell_join(
        [
            "python",
            "skills/gh-autopilot/scripts/run_autopilot_loop.py",
            "--repo",
            ".",
            "--output-dir",
            str(output_dir),
            "--pr",
            str(pr_number),
            "finalize-cycle",
        ]
    )


def build_status_command(output_dir: Path, pr_number: int) -> str:
    return shell_join(
        [
            "python",
            "skills/gh-autopilot/scripts/run_autopilot_loop.py",
            "--repo",
            ".",
            "--output-dir",
            str(output_dir),
            "--pr",
            str(pr_number),
            "status",
        ]
    )


def build_assert_drained_command(output_dir: Path, pr_number: int) -> str:
    return shell_join(
        [
            "python",
            "skills/gh-autopilot/scripts/run_autopilot_loop.py",
            "--repo",
            ".",
            "--output-dir",
            str(output_dir),
            "--pr",
            str(pr_number),
            "assert-drained",
        ]
    )


def normalize_timing_payload(raw_timing: Any) -> dict[str, int]:
    defaults = {
        "initial_sleep_seconds": 300,
        "poll_interval_seconds": 45,
        "max_wait_seconds": 2400,
    }
    if not isinstance(raw_timing, dict):
        return defaults.copy()

    normalized = defaults.copy()
    for key, fallback in defaults.items():
        value = raw_timing.get(key)
        if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
            normalized[key] = fallback
            continue
        normalized[key] = value
    return normalized


def extract_pr_number(state: dict[str, Any]) -> int | None:
    pr_payload = state.get("pr")
    if not isinstance(pr_payload, dict):
        return None
    raw_number = pr_payload.get("number")
    if isinstance(raw_number, bool):
        return None
    if isinstance(raw_number, int):
        return raw_number
    if isinstance(raw_number, str) and raw_number.isdigit():
        return int(raw_number)
    return None


def build_resume_command(
    *,
    state: dict[str, Any],
    output_dir: Path,
    pr_number: int,
    stage2_max_wait_seconds: int = DEFAULT_STAGE2_MAX_WAIT_SECONDS,
) -> str:
    status = str(state.get("status") or "")
    if status in {STATUS_AWAITING_ADDRESS, STATUS_AWAITING_TRIAGE}:
        return build_finalize_cycle_command(output_dir, pr_number)
    if status == STATUS_COMPLETED_NO_COMMENTS:
        return build_assert_drained_command(output_dir, pr_number)
    if (
        status == STATUS_TIMEOUT
        and state.get("last_timeout_reason") == TIMEOUT_REASON_STAGE2_MAX_WAIT_REACHED
    ):
        return build_status_command(output_dir, pr_number)
    return build_run_stage2_loop_command(
        output_dir,
        pr_number,
        normalize_timing_payload(state.get("timing")),
        stage2_max_wait_seconds=stage2_max_wait_seconds,
    )


def attach_resume_command(
    result: dict[str, Any],
    *,
    state: dict[str, Any],
    output_dir: Path,
    pr_number: int,
    stage2_max_wait_seconds: int = DEFAULT_STAGE2_MAX_WAIT_SECONDS,
) -> dict[str, Any]:
    result["resume_command"] = build_resume_command(
        state=state,
        output_dir=output_dir,
        pr_number=pr_number,
        stage2_max_wait_seconds=stage2_max_wait_seconds,
    )
    return result


def context_doc_paths(output_dir: Path) -> dict[str, Path]:
    return {
        "context": default_context_file(output_dir),
    }


def load_required_json(path: Path, *, label: str) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"{label} file not found: {path}")
    raw = path.read_text(encoding="utf-8")
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError(f"{label} is not valid JSON: {path}") from exc
    if not isinstance(payload, dict):
        raise ValueError(f"{label} must contain a JSON object: {path}")
    return payload


def require_int(value: Any, *, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{field} must be an integer")
    return value


def summarize_feedback_coverage(feedback_payload: dict[str, Any]) -> dict[str, int]:
    copilot_threads = feedback_payload.get("copilot_threads")
    if not isinstance(copilot_threads, list):
        raise ValueError("cycle.json is missing list field `copilot_threads`")

    total_threads = 0
    total_comments = 0
    eligible_threads = 0
    eligible_comments = 0
    for idx, thread in enumerate(copilot_threads, start=1):
        if not isinstance(thread, dict):
            raise ValueError(f"cycle.json has non-object thread at index {idx}")
        comments = thread.get("comments")
        if comments is None:
            comments = []
        if not isinstance(comments, list):
            raise ValueError(
                f"cycle.json thread index {idx} has non-list `comments` value"
            )
        total_threads += 1
        total_comments += len(comments)
        if bool(thread.get("eligible_for_addressing")):
            eligible_threads += 1
            eligible_comments += len(comments)

    return {
        "total_threads": total_threads,
        "total_comments": total_comments,
        "eligible_threads": eligible_threads,
        "eligible_comments": eligible_comments,
    }


def validate_summary_comment_consistency(
    cycle_payload: dict[str, Any], *, coverage: dict[str, int]
) -> None:
    parsed_summary = cycle_payload.get("parsed_summary")
    if not isinstance(parsed_summary, dict):
        return
    generated_comments = parsed_summary.get("generated_comments")
    if not isinstance(generated_comments, int):
        return
    if generated_comments > 0 and coverage["total_comments"] == 0:
        raise ValueError(
            "cycle.json summary indicates generated comments but no review comments were captured; "
            "refresh cycle artifacts before finalize-cycle"
        )


def collect_all_thread_ids(feedback_payload: dict[str, Any]) -> set[str]:
    copilot_threads = feedback_payload.get("copilot_threads")
    if not isinstance(copilot_threads, list):
        raise ValueError("cycle.json is missing list field `copilot_threads`")

    thread_ids: set[str] = set()
    for idx, thread in enumerate(copilot_threads, start=1):
        if not isinstance(thread, dict):
            raise ValueError(f"cycle.json has non-object thread at index {idx}")
        thread_id = thread.get("thread_id")
        if not isinstance(thread_id, str) or not thread_id:
            raise ValueError(
                f"cycle.json thread index {idx} missing valid `thread_id`"
            )
        if thread_id in thread_ids:
            raise ValueError(f"cycle.json has duplicate thread_id `{thread_id}`")
        thread_ids.add(thread_id)
    return thread_ids


def collect_feedback_comments(feedback_payload: dict[str, Any]) -> list[dict[str, str]]:
    copilot_threads = feedback_payload.get("copilot_threads")
    if not isinstance(copilot_threads, list):
        raise ValueError("cycle.json is missing list field `copilot_threads`")

    comments: list[dict[str, str]] = []
    seen_comment_ids: set[str] = set()
    for thread_idx, thread in enumerate(copilot_threads, start=1):
        if not isinstance(thread, dict):
            raise ValueError(f"cycle.json has non-object thread at index {thread_idx}")
        thread_id = thread.get("thread_id")
        if not isinstance(thread_id, str) or not thread_id:
            raise ValueError(
                f"cycle.json thread index {thread_idx} missing valid `thread_id`"
            )

        raw_comments = thread.get("comments")
        if raw_comments is None:
            raw_comments = []
        if not isinstance(raw_comments, list):
            raise ValueError(
                f"cycle.json thread index {thread_idx} has non-list `comments` value"
            )
        for comment_idx, comment in enumerate(raw_comments, start=1):
            if not isinstance(comment, dict):
                raise ValueError(
                    "cycle.json thread index "
                    f"{thread_idx} comment index {comment_idx} is not an object"
                )
            comment_id = comment.get("id")
            if not isinstance(comment_id, str) or not comment_id:
                raise ValueError(
                    "cycle.json thread index "
                    f"{thread_idx} comment index {comment_idx} missing valid `id`"
                )
            if comment_id in seen_comment_ids:
                raise ValueError(f"cycle.json has duplicate comment id `{comment_id}`")
            seen_comment_ids.add(comment_id)

            created_at = comment.get("created_at")
            if not isinstance(created_at, str) or not created_at:
                raise ValueError(
                    f"cycle.json comment `{comment_id}` missing valid `created_at`"
                )
            created_at_parsed = parse_iso(created_at)
            if created_at_parsed is None:
                raise ValueError(
                    f"cycle.json comment `{comment_id}` has invalid `created_at` timestamp"
                )

            comments.append(
                {
                    "comment_id": comment_id,
                    "thread_id": thread_id,
                    "created_at": created_at,
                }
            )

    return comments


def validate_comment_statuses(
    address_result: dict[str, Any],
    *,
    state_cycle: int,
    feedback_comments: list[dict[str, str]],
) -> dict[str, Any]:
    raw_statuses = address_result.get("comment_statuses")
    if not isinstance(raw_statuses, list):
        raise ValueError(
            "cycle.json addressing missing list field `comment_statuses` for per-comment tracking"
        )

    feedback_by_comment_id = {item["comment_id"]: item for item in feedback_comments}
    seen_comment_ids: set[str] = set()
    normalized_statuses: list[dict[str, Any]] = []
    action_count = 0
    no_action_count = 0

    for idx, raw in enumerate(raw_statuses, start=1):
        if not isinstance(raw, dict):
            raise ValueError(
                f"cycle.json addressing comment_statuses[{idx}] must be an object"
            )
        comment_id = raw.get("comment_id")
        if not isinstance(comment_id, str) or not comment_id:
            raise ValueError(
                f"cycle.json addressing comment_statuses[{idx}] missing valid `comment_id`"
            )
        if comment_id in seen_comment_ids:
            raise ValueError(
                f"cycle.json addressing has duplicate comment status for `{comment_id}`"
            )
        seen_comment_ids.add(comment_id)

        feedback_comment = feedback_by_comment_id.get(comment_id)
        if feedback_comment is None:
            raise ValueError(
                f"cycle.json addressing comment status references unknown comment `{comment_id}`"
            )

        cycle_value = raw.get("cycle")
        if cycle_value != state_cycle:
            raise ValueError(
                f"comment `{comment_id}` has cycle `{cycle_value}` but expected `{state_cycle}`"
            )

        status = raw.get("status")
        if status not in {"action", "no_action"}:
            raise ValueError(
                f"comment `{comment_id}` has invalid status `{status}`; expected action or no_action"
            )
        if status == "action":
            action_count += 1
        else:
            no_action_count += 1

        thread_id = raw.get("thread_id")
        if thread_id != feedback_comment["thread_id"]:
            raise ValueError(
                f"comment `{comment_id}` thread_id mismatch with cycle.json"
            )

        created_at = raw.get("created_at")
        if created_at != feedback_comment["created_at"]:
            raise ValueError(
                f"comment `{comment_id}` created_at mismatch with cycle.json"
            )
        created_at_parsed = parse_iso(created_at)
        if created_at_parsed is None:
            raise ValueError(
                f"comment `{comment_id}` has invalid created_at timestamp in comment_statuses"
            )

        normalized_statuses.append(
            {
                "comment_id": comment_id,
                "thread_id": thread_id,
                "created_at": created_at,
                "cycle": state_cycle,
                "status": status,
            }
        )

    missing_comment_ids = sorted(set(feedback_by_comment_id) - seen_comment_ids)
    if missing_comment_ids:
        raise ValueError(
            "cycle.json addressing is missing comment statuses for: "
            + ", ".join(missing_comment_ids)
        )

    expected_order = sorted(
        normalized_statuses, key=lambda item: (item["created_at"], item["comment_id"])
    )
    normalized_ids = [item["comment_id"] for item in normalized_statuses]
    expected_ids = [item["comment_id"] for item in expected_order]
    if normalized_ids != expected_ids:
        raise ValueError(
            "cycle.json addressing comment_statuses must be sorted chronologically by created_at"
        )

    return {
        "comment_statuses": normalized_statuses,
        "action_comments": action_count,
        "no_action_comments": no_action_count,
    }


def validate_thread_response_coverage(
    address_result: dict[str, Any], *, all_thread_ids: set[str]
) -> dict[str, int]:
    thread_responses = address_result.get("thread_responses")
    if not isinstance(thread_responses, list):
        raise ValueError(
            "cycle.json addressing missing list field `thread_responses` for review-thread coverage"
        )

    seen_thread_ids: set[str] = set()
    actionable_threads = 0
    non_actionable_threads = 0

    for idx, item in enumerate(thread_responses, start=1):
        if not isinstance(item, dict):
            raise ValueError(
                f"cycle.json addressing thread_responses[{idx}] must be an object"
            )
        thread_id = item.get("thread_id")
        if not isinstance(thread_id, str) or not thread_id:
            raise ValueError(
                f"cycle.json addressing thread_responses[{idx}] missing valid `thread_id`"
            )
        if thread_id in seen_thread_ids:
            raise ValueError(
                f"cycle.json addressing contains duplicate thread response for `{thread_id}`"
            )
        seen_thread_ids.add(thread_id)
        if thread_id not in all_thread_ids:
            raise ValueError(
                f"cycle.json addressing thread response includes unknown thread `{thread_id}`"
            )

        classification = item.get("classification")
        if classification == "actionable":
            actionable_threads += 1
            if item.get("resolved") is not True:
                raise ValueError(
                    f"actionable thread `{thread_id}` must be marked resolved=true before finalize-cycle"
                )
        elif classification == "non-actionable":
            non_actionable_threads += 1
            if item.get("rationale_replied") is not True:
                raise ValueError(
                    f"non-actionable thread `{thread_id}` must set rationale_replied=true before finalize-cycle"
                )
        else:
            raise ValueError(
                f"thread `{thread_id}` has invalid classification `{classification}`; expected actionable or non-actionable"
            )

    missing = sorted(all_thread_ids - seen_thread_ids)
    if missing:
        raise ValueError(
            "cycle.json addressing is missing responses for review threads: "
            + ", ".join(missing)
        )

    return {
        "actionable_threads": actionable_threads,
        "non_actionable_threads": non_actionable_threads,
    }


def validate_finalize_artifacts(
    output_dir: Path, *, state: dict[str, Any]
) -> dict[str, Any]:
    cycle_path = default_cycle_file(output_dir)
    cycle_payload = load_required_json(cycle_path, label="cycle")
    addressing = cycle_payload.get("addressing")
    if not isinstance(addressing, dict):
        raise ValueError(
            "cycle.json missing object field `addressing`; Stage 3 worker must populate it before finalize-cycle"
        )

    if addressing.get("status") != "ready_for_finalize":
        raise ValueError(
            "cycle.json addressing.status must be ready_for_finalize before finalize-cycle"
        )
    if addressing.get("pushed_once") is not True:
        raise ValueError(
            "cycle.json addressing.pushed_once must be true before finalize-cycle"
        )

    pending_review_id = state.get("pending_review_id")
    if addressing.get("review_id") != pending_review_id:
        raise ValueError(
            "cycle.json addressing.review_id does not match state pending_review_id"
        )
    state_cycle = int(state.get("cycle"))
    if addressing.get("cycle") != state_cycle:
        raise ValueError("cycle.json addressing.cycle does not match current state cycle")

    coverage = summarize_feedback_coverage(cycle_payload)
    validate_summary_comment_consistency(cycle_payload, coverage=coverage)
    all_thread_ids = collect_all_thread_ids(cycle_payload)
    feedback_comments = collect_feedback_comments(cycle_payload)
    thread_response_summary = validate_thread_response_coverage(
        addressing, all_thread_ids=all_thread_ids
    )
    comment_status_summary = validate_comment_statuses(
        addressing,
        state_cycle=state_cycle,
        feedback_comments=feedback_comments,
    )

    threads_summary = addressing.get("threads")
    if not isinstance(threads_summary, dict):
        raise ValueError("cycle.json addressing missing object field `threads`")
    addressed_threads = require_int(
        threads_summary.get("addressed"), field="threads.addressed"
    )
    rejected_threads = require_int(
        threads_summary.get("rejected_with_rationale"),
        field="threads.rejected_with_rationale",
    )
    needs_clarification_threads = require_int(
        threads_summary.get("needs_clarification"),
        field="threads.needs_clarification",
    )
    if needs_clarification_threads != 0:
        raise ValueError(
            "cycle.json addressing indicates unresolved threads (threads.needs_clarification must be 0)"
        )
    if addressed_threads + rejected_threads != coverage["total_threads"]:
        raise ValueError(
            "cycle.json addressing thread totals do not cover all Copilot review threads; "
            "cannot re-request reviewer until the full batch is addressed"
        )
    if addressed_threads != thread_response_summary["actionable_threads"]:
        raise ValueError(
            "cycle.json addressing threads.addressed must match actionable thread_responses count"
        )
    if rejected_threads != thread_response_summary["non_actionable_threads"]:
        raise ValueError(
            "cycle.json addressing threads.rejected_with_rationale must match non-actionable thread_responses count"
        )

    comments_summary = addressing.get("comments")
    if not isinstance(comments_summary, dict):
        raise ValueError(
            "cycle.json addressing missing object field `comments` with coverage counts"
        )
    addressed_or_rationalized_comments = require_int(
        comments_summary.get("addressed_or_rationalized"),
        field="comments.addressed_or_rationalized",
    )
    needs_clarification_comments = require_int(
        comments_summary.get("needs_clarification"),
        field="comments.needs_clarification",
    )
    if needs_clarification_comments != 0:
        raise ValueError(
            "cycle.json addressing indicates unresolved comments (comments.needs_clarification must be 0)"
        )
    if addressed_or_rationalized_comments != coverage["total_comments"]:
        raise ValueError(
            "cycle.json addressing comment totals do not cover all Copilot review comments; "
            "cannot re-request reviewer until the full batch is addressed"
        )
    if addressed_or_rationalized_comments != len(comment_status_summary["comment_statuses"]):
        raise ValueError(
            "cycle.json addressing comments.addressed_or_rationalized must match comment_statuses count"
        )

    return {
        "cycle_json": str(cycle_path),
        "total_threads": coverage["total_threads"],
        "total_comments": coverage["total_comments"],
        "eligible_threads": coverage["eligible_threads"],
        "eligible_comments": coverage["eligible_comments"],
        "actionable_threads": thread_response_summary["actionable_threads"],
        "non_actionable_threads": thread_response_summary[
            "non_actionable_threads"
        ],
        "comment_statuses": comment_status_summary["comment_statuses"],
        "action_comments": comment_status_summary["action_comments"],
        "no_action_comments": comment_status_summary["no_action_comments"],
    }


def write_context_markdown(
    context_file: Path,
    *,
    title: str,
    memory_title: str,
    state: dict[str, Any],
    pr: GhPrRef,
    phase: str,
    notes: list[str],
    tasks: list[ChecklistTask],
    memory_bullets: list[str],
    artifacts: dict[str, str],
    next_commands: list[str],
) -> None:
    context_file.parent.mkdir(parents=True, exist_ok=True)
    timeout_reason = state.get("last_timeout_reason") or "none"
    status_header = (
        f"phase={phase} | cycle={state['cycle']} | status={state['status']} "
        f"| timeout_reason={timeout_reason}"
    )
    lines = [
        "# GH Autopilot Context",
        "",
        f"- Updated: {now_iso()}",
        f"- PR: #{pr.number} ({pr.url})",
        f"- Status Header: {status_header}",
        f"- Summary: {title}",
        "",
        "## Context Contract",
        "",
        f"- Format version: {CONTEXT_FORMAT_VERSION}",
        "- Checklist semantics: `[x]` means completed for the current phase, `[ ]` means pending.",
        "- Section order is fixed for session-to-session stability.",
        "",
        "## Next Actions",
        "",
    ]
    lines.extend(f"- {task.render()}" for task in tasks)
    lines.extend(
        [
            "",
            "## Notes",
            "",
        ]
    )
    lines.extend(f"- {note}" for note in notes)
    lines.extend(
        [
            "",
            "## Snapshot",
            "",
            f"- {memory_title}",
        ]
    )
    lines.extend(f"- {bullet}" for bullet in memory_bullets)
    lines.extend(
        [
            "",
            "## State",
            "",
        ]
    )
    lines.extend(
        [
            f"- Pending review id: {state.get('pending_review_id')}",
            f"- Last processed review id: {state.get('last_processed_review_id')}",
        ]
    )
    lines.extend(
        [
            "",
            "## Artifacts",
            "",
        ]
    )
    if artifacts:
        for name, path in sorted(artifacts.items()):
            lines.append(f"- {name}: `{path}`")
    else:
        lines.append("- None")
    lines.extend(
        [
            "",
            "## Suggested Commands",
            "",
        ]
    )
    lines.extend(f"- `{command}`" for command in next_commands)
    lines.append("")
    context_file.write_text("\n".join(lines), encoding="utf-8")


def write_comment_status_history(
    output_dir: Path,
    *,
    review_id: str,
    comment_statuses: list[dict[str, Any]],
) -> Path:
    history_file = default_comment_status_history_file(output_dir)
    existing_comments: list[dict[str, Any]] = []

    if history_file.exists():
        payload = load_required_json(history_file, label="comment-status-history")
        raw_existing = payload.get("comments")
        if raw_existing is None:
            raw_existing = []
        if not isinstance(raw_existing, list):
            raise ValueError(
                "comment-status-history.json must have list field `comments`"
            )
        for idx, item in enumerate(raw_existing, start=1):
            if not isinstance(item, dict):
                raise ValueError(
                    f"comment-status-history.json comments[{idx}] must be an object"
                )
            comment_id = item.get("comment_id")
            created_at = item.get("created_at")
            if not isinstance(comment_id, str) or not comment_id:
                raise ValueError(
                    f"comment-status-history.json comments[{idx}] missing valid `comment_id`"
                )
            if not isinstance(created_at, str) or parse_iso(created_at) is None:
                raise ValueError(
                    f"comment-status-history.json comments[{idx}] has invalid `created_at`"
                )
            existing_comments.append(item)

    by_comment_id: dict[str, dict[str, Any]] = {
        item["comment_id"]: item for item in existing_comments
    }
    updated_at = now_iso()
    for item in comment_statuses:
        by_comment_id[item["comment_id"]] = {
            "comment_id": item["comment_id"],
            "thread_id": item["thread_id"],
            "review_id": review_id,
            "cycle": item["cycle"],
            "status": item["status"],
            "created_at": item["created_at"],
            "updated_at": updated_at,
        }

    merged = sorted(
        by_comment_id.values(),
        key=lambda entry: (entry["created_at"], entry["comment_id"]),
    )

    payload = {
        "version": 1,
        "updated_at": updated_at,
        "comments": merged,
    }
    history_file.parent.mkdir(parents=True, exist_ok=True)
    history_file.write_text(render_json(payload) + "\n", encoding="utf-8")
    return history_file


def update_context_documents(
    output_dir: Path,
    *,
    state: dict[str, Any],
    pr: GhPrRef,
    phase: str,
    artifacts: dict[str, str] | None = None,
) -> dict[str, str]:
    paths = context_doc_paths(output_dir)
    timing = state["timing"]
    status_cmd = build_status_command(output_dir, pr.number)
    assert_drained_cmd = build_assert_drained_command(output_dir, pr.number)
    run_cycle_cmd = build_run_cycle_command(output_dir, pr.number, timing)
    run_stage2_loop_cmd = build_run_stage2_loop_command(
        output_dir, pr.number, timing
    )
    finalize_cmd = build_finalize_cycle_command(output_dir, pr.number)
    cycle = state["cycle"]
    artifact_map = artifacts or {}

    if phase == STATUS_INITIALIZED:
        title = "Initialization Complete"
        tasks = [
            ChecklistTask("Loop initialized and context seeded.", done=True),
            ChecklistTask("Start Stage 2 monitor loop", command=run_stage2_loop_cmd),
            ChecklistTask("Review `cycle.json` when a cycle returns `awaiting_address`."),
            ChecklistTask(
                "Reply on Copilot thread for non-actionable comments with technical rationale."
            ),
            ChecklistTask(
                "Finalize addressed batch and re-request Copilot", command=finalize_cmd
            ),
            ChecklistTask(
                "Before declaring loop complete, confirm drain guard passes",
                command=assert_drained_cmd,
            ),
        ]
        notes = [
            "Loop initialized and ready for first review polling cycle.",
            "If this branch already had an open PR, continue without PR creation.",
        ]
        memory_title = f"Initialized loop for PR #{pr.number}"
    elif phase == STATUS_AWAITING_ADDRESS:
        title = f"Cycle {cycle} Requires Addressing"
        tasks = [
            ChecklistTask("New Copilot review captured for this cycle.", done=True),
            ChecklistTask("Read `cycle.json`."),
            ChecklistTask(
                "Classify each thread as actionable/non-actionable/needs-clarification."
            ),
            ChecklistTask("Apply fixes for actionable threads and run validation."),
            ChecklistTask(
                "Reply on Copilot thread for non-actionable comments with rationale."
            ),
            ChecklistTask(
                "Confirm all Copilot review comments are addressed or rejected-with-rationale."
            ),
            ChecklistTask(
                "Do not finalize or re-request reviewer per thread; finish the full batch first."
            ),
            ChecklistTask("Push one batch for this cycle."),
            ChecklistTask("Finalize cycle", command=finalize_cmd),
            ChecklistTask(
                "Confirm no pending address-required state remains",
                command=assert_drained_cmd,
            ),
        ]
        notes = [
            "Copilot returned comments requiring updates before next review round.",
            "Do not re-request reviewer until finalize-cycle after full-batch completion.",
        ]
        memory_title = f"Cycle {cycle} entered awaiting_address"
    elif phase == STATUS_AWAITING_TRIAGE:
        title = f"Cycle {cycle} Needs Triage"
        tasks = [
            ChecklistTask("New Copilot review captured and triage is required.", done=True),
            ChecklistTask("Read `cycle.json`."),
            ChecklistTask("Determine whether comments are actionable or non-actionable."),
            ChecklistTask("Ask clarification if thread intent is unclear."),
            ChecklistTask("After triage and updates, push once and finalize cycle."),
            ChecklistTask("Finalize cycle", command=finalize_cmd),
            ChecklistTask(
                "Confirm no pending address-required state remains",
                command=assert_drained_cmd,
            ),
        ]
        notes = [
            "Copilot review arrived without clear comment signal; manual triage is required.",
            "Keep per-thread classification explicit in cycle addressing records.",
        ]
        memory_title = f"Cycle {cycle} entered awaiting_triage"
    elif phase == STATUS_TIMEOUT:
        title = f"Cycle {cycle} Timed Out"
        tasks = [
            ChecklistTask(
                "Cycle wait window elapsed without a new Copilot review.", done=True
            ),
            ChecklistTask(
                "Inspect `state.last_wait` and the latest timeout event to confirm Copilot is stuck."
            ),
            ChecklistTask(
                "Continue Stage 2 waiting unless the configured Stage 2 max-wait budget has been reached."
            ),
            ChecklistTask(
                "Resume long-wait Stage 2 loop", command=run_stage2_loop_cmd
            ),
            ChecklistTask(
                "For one-off diagnostics only, single-cycle wait remains available",
                command=run_cycle_cmd,
            ),
        ]
        notes = [
            "No new Copilot review arrived in this cycle wait window.",
            "Use run-stage2-loop to keep retrying until the Stage 2 max-wait budget is exhausted.",
        ]
        memory_title = f"Cycle {cycle} timed out waiting for review"
    elif phase == STATUS_COMPLETED_NO_COMMENTS:
        title = f"Cycle {cycle} Completed: No Comments"
        tasks = [
            ChecklistTask("Copilot reported no comments for this PR.", done=True),
            ChecklistTask(
                "Confirm loop is drained before stop", command=assert_drained_cmd
            ),
            ChecklistTask(
                "Stop loop or archive context artifacts if no further iteration is needed."
            ),
        ]
        notes = [
            "Terminal success condition reached: Copilot generated no comments.",
        ]
        memory_title = f"Cycle {cycle} completed with no comments"
    elif phase == PHASE_FINALIZED:
        title = f"Cycle {cycle} Finalized"
        reviewer_done = state.get("status") == STATUS_REREQUESTED
        tasks = [
            ChecklistTask("Finalize-cycle completed for the prior batch.", done=True),
            ChecklistTask(
                "Copilot reviewer re-request completed.",
                done=reviewer_done,
            ),
            ChecklistTask("Start next Stage 2 monitor loop for new Copilot response."),
            ChecklistTask("Run Stage 2 loop", command=run_stage2_loop_cmd),
            ChecklistTask(
                "Confirm drain guard status before reporting completion",
                command=assert_drained_cmd,
            ),
        ]
        notes = [
            "Prior cycle was finalized and reviewer re-request (if enabled) has completed.",
        ]
        memory_title = f"Finalized cycle {cycle}"
    else:
        title = f"Cycle {cycle} Status Update"
        tasks = [
            ChecklistTask(f"Status transitioned to `{phase}`.", done=True),
            ChecklistTask("Check state", command=status_cmd),
            ChecklistTask("Check drain guard", command=assert_drained_cmd),
            ChecklistTask("Continue loop", command=run_cycle_cmd),
        ]
        notes = [f"Status transitioned to `{phase}`."]
        memory_title = f"Status update for cycle {cycle}"

    memory_bullets = [
        f"status={state['status']}",
        f"cycle={cycle}",
        f"pending_review_id={state.get('pending_review_id')}",
        f"last_processed_review_id={state.get('last_processed_review_id')}",
    ]
    timeout_reason = state.get("last_timeout_reason")
    if timeout_reason:
        memory_bullets.append(f"last_timeout_reason={timeout_reason}")
    if artifact_map:
        memory_bullets.append(
            "artifacts="
            + ", ".join(
                f"{key}:{value}" for key, value in sorted(artifact_map.items())
            )
        )

    next_commands = [status_cmd, assert_drained_cmd]
    if phase in {STATUS_INITIALIZED, PHASE_FINALIZED, STATUS_TIMEOUT}:
        next_commands.append(run_stage2_loop_cmd)
        next_commands.append(run_cycle_cmd)
    if phase in {STATUS_AWAITING_ADDRESS, STATUS_AWAITING_TRIAGE}:
        next_commands.append(finalize_cmd)

    write_context_markdown(
        paths["context"],
        title=title,
        memory_title=memory_title,
        state=state,
        pr=pr,
        phase=phase,
        notes=notes,
        tasks=tasks,
        memory_bullets=memory_bullets,
        artifacts=artifact_map,
        next_commands=next_commands,
    )
    return {name: str(path) for name, path in paths.items()}


def init_state(
    store: AutopilotStateStore,
    *,
    pr: GhPrRef,
    initial_sleep_seconds: int,
    poll_interval_seconds: int,
    max_wait_seconds: int,
    force: bool,
) -> dict[str, Any]:
    if store.state_file.exists() and not force:
        raise FileExistsError(
            f"state already exists at {store.state_file}; use --force to reset."
        )
    state = {
        "version": STATE_VERSION,
        "status": STATUS_INITIALIZED,
        "cycle": 0,
        "pr": pr.as_dict(),
        "last_processed_review_id": None,
        "last_processed_review_submitted_at": None,
        "pending_review_id": None,
        "pending_review_submitted_at": None,
        "last_timeout_reason": None,
        "last_wait": None,
        "timing": {
            "initial_sleep_seconds": initial_sleep_seconds,
            "poll_interval_seconds": poll_interval_seconds,
            "max_wait_seconds": max_wait_seconds,
        },
        "updated_at": now_iso(),
    }
    store.save(state)
    store.append_event("initialized", {"pr": pr.as_dict()})
    return state


def ensure_state_pr_matches(state: dict[str, Any], pr: GhPrRef) -> None:
    state_pr = state["pr"]
    if int(state_pr["number"]) != pr.number:
        raise ValueError(
            f"state PR mismatch: state has #{state_pr['number']} but resolved #{pr.number}"
        )


def run_cycle(
    client: GhClient,
    store: AutopilotStateStore,
    *,
    pr: GhPrRef,
    output_dir: Path,
    monitor_file: Path,
    initial_sleep_seconds: int,
    poll_interval_seconds: int,
    max_wait_seconds: int,
) -> int:
    _ = monitor_file  # monitor snapshots are now kept in state.last_wait/event payloads.
    state = store.load()
    ensure_state_pr_matches(state, pr)
    if state["status"] == STATUS_AWAITING_ADDRESS:
        raise ValueError(
            "state is awaiting_address; complete addressing and run finalize-cycle first."
        )
    if state["status"] == STATUS_AWAITING_TRIAGE:
        raise ValueError(
            "state is awaiting_triage; classify cycle result and run finalize-cycle first."
        )
    if state["status"] in TERMINAL_STATUSES:
        context_docs = update_context_documents(
            output_dir,
            state=state,
            pr=pr,
            phase=state["status"],
        )
        result = attach_resume_command(
            {
                "status": state["status"],
                "message": "state is already terminal; re-init to start over",
                "state_file": str(store.state_file),
                "context_docs": context_docs,
            },
            state=state,
            output_dir=output_dir,
            pr_number=pr.number,
        )
        print(
            render_json(result)
        )
        return 0

    state["status"] = transition_status(state["status"], EVENT_BEGIN_CYCLE_WAIT)
    state["last_timeout_reason"] = None
    store.save(state)
    store.append_event("cycle_waiting", {"cycle": state["cycle"]})

    wait_status, wait_payload = wait_for_new_review(
        client,
        pr=pr,
        exclude_review_id=state.get("last_processed_review_id"),
        initial_sleep_seconds=initial_sleep_seconds,
        poll_interval_seconds=poll_interval_seconds,
        max_wait_seconds=max_wait_seconds,
    )

    if wait_status == "timeout":
        state["status"] = transition_status(state["status"], EVENT_CYCLE_TIMEOUT)
        state["last_timeout_reason"] = TIMEOUT_REASON_CYCLE_MAX_WAIT_REACHED
        state["last_wait"] = wait_payload
        store.save(state)
        context_docs = update_context_documents(
            output_dir,
            state=state,
            pr=pr,
            phase=STATUS_TIMEOUT,
        )
        store.append_event(
            "cycle_timeout",
            {
                "cycle": state["cycle"],
                "wait": wait_payload,
            },
        )
        result = attach_resume_command(
            {
                "status": STATUS_TIMEOUT,
                "reason": "no_new_copilot_review_before_deadline",
                "timeout_reason": state["last_timeout_reason"],
                "wait": wait_payload,
                "context_docs": context_docs,
            },
            state=state,
            output_dir=output_dir,
            pr_number=pr.number,
        )
        print(
            render_json(result)
        )
        return 3

    review = wait_payload["copilot_review"]
    threads = fetch_all_threads(client, pr)
    normalized_threads = normalize_threads(threads, review_id=review.get("id"))
    next_status, summary = detect_cycle_status(review, normalized_threads)

    artifacts = write_cycle_artifact(
        output_dir,
        cycle=state["cycle"],
        pr=pr,
        review=review,
        status=next_status,
        summary=summary,
        threads=normalized_threads,
    )

    if next_status == STATUS_COMPLETED_NO_COMMENTS:
        state["status"] = transition_status(state["status"], EVENT_CYCLE_NO_COMMENTS)
        state["pending_review_id"] = None
        state["pending_review_submitted_at"] = None
        state["last_timeout_reason"] = None
        state["last_wait"] = wait_payload
        store.save(state)
        context_docs = update_context_documents(
            output_dir,
            state=state,
            pr=pr,
            phase=STATUS_COMPLETED_NO_COMMENTS,
            artifacts=artifacts,
        )
        store.append_event(
            "cycle_completed_no_comments",
            {
                "cycle": state["cycle"],
                "review_id": review["id"],
                "artifacts": artifacts,
            },
        )
        result = attach_resume_command(
            {
                "status": STATUS_COMPLETED_NO_COMMENTS,
                "cycle": state["cycle"],
                "review_id": review["id"],
                "artifacts": artifacts,
                "wait": wait_payload,
                "context_docs": context_docs,
            },
            state=state,
            output_dir=output_dir,
            pr_number=pr.number,
        )
        print(
            render_json(result)
        )
        return 0

    event = (
        EVENT_CYCLE_NEEDS_ADDRESS
        if next_status == STATUS_AWAITING_ADDRESS
        else EVENT_CYCLE_NEEDS_TRIAGE
    )
    state["status"] = transition_status(state["status"], event)
    state["pending_review_id"] = review["id"]
    state["pending_review_submitted_at"] = review["submitted_at"]
    state["last_timeout_reason"] = None
    state["last_wait"] = wait_payload
    store.save(state)
    context_docs = update_context_documents(
        output_dir,
        state=state,
        pr=pr,
        phase=next_status,
        artifacts=artifacts,
    )
    store.append_event(
        "cycle_action_required",
        {
            "cycle": state["cycle"],
            "review_id": review["id"],
            "status": next_status,
            "artifacts": artifacts,
        },
    )
    result = attach_resume_command(
        {
            "status": next_status,
            "cycle": state["cycle"],
            "review_id": review["id"],
            "artifacts": artifacts,
            "wait": wait_payload,
            "context_docs": context_docs,
        },
        state=state,
        output_dir=output_dir,
        pr_number=pr.number,
    )
    print(
        render_json(result)
    )
    return 10


def run_stage2_loop(
    client: GhClient,
    store: AutopilotStateStore,
    *,
    pr: GhPrRef,
    output_dir: Path,
    monitor_file: Path,
    initial_sleep_seconds: int,
    poll_interval_seconds: int,
    max_wait_seconds: int,
    stage2_max_wait_seconds: int,
) -> int:
    if stage2_max_wait_seconds <= 0:
        raise ValueError("--stage2-max-wait-seconds must be > 0")

    try:
        state = store.load()
        ensure_state_pr_matches(state, pr)
    except FileNotFoundError:
        state = init_state(
            store,
            pr=pr,
            initial_sleep_seconds=initial_sleep_seconds,
            poll_interval_seconds=poll_interval_seconds,
            max_wait_seconds=max_wait_seconds,
            force=False,
        )
        update_context_documents(
            output_dir,
            state=state,
            pr=pr,
            phase=STATUS_INITIALIZED,
        )

    timing_payload = {
        "initial_sleep_seconds": initial_sleep_seconds,
        "poll_interval_seconds": poll_interval_seconds,
        "max_wait_seconds": max_wait_seconds,
    }
    if state.get("timing") != timing_payload:
        state["timing"] = timing_payload
        store.save(state)
        store.append_event(
            "stage2_loop_timing_updated",
            {
                "cycle": state["cycle"],
                "timing": timing_payload,
            },
        )

    start = time.monotonic()
    deadline = start + stage2_max_wait_seconds
    store.append_event(
        "stage2_loop_started",
        {
            "cycle": state["cycle"],
            "stage2_max_wait_seconds": stage2_max_wait_seconds,
            "timing": {
                "initial_sleep_seconds": initial_sleep_seconds,
                "poll_interval_seconds": poll_interval_seconds,
                "max_wait_seconds": max_wait_seconds,
            },
        },
    )

    timeout_retries = 0
    run_attempts = 0

    while True:
        state = store.load()
        ensure_state_pr_matches(state, pr)
        status = state.get("status")

        now = time.monotonic()
        remaining_seconds = int(deadline - now)

        if status in {STATUS_AWAITING_ADDRESS, STATUS_AWAITING_TRIAGE}:
            result = {
                "status": status,
                "reason": "addressing_required",
                "cycle": state.get("cycle"),
                "pending_review_id": state.get("pending_review_id"),
                "timing": {
                    "stage2_max_wait_seconds": stage2_max_wait_seconds,
                    "elapsed_seconds": int(now - start),
                    "run_attempts": run_attempts,
                    "timeout_retries": timeout_retries,
                },
            }
            attach_resume_command(
                result,
                state=state,
                output_dir=output_dir,
                pr_number=pr.number,
                stage2_max_wait_seconds=stage2_max_wait_seconds,
            )
            store.append_event("stage2_loop_action_required", result)
            print(render_json(result))
            return 10

        if status == STATUS_COMPLETED_NO_COMMENTS:
            drained_exit, drained_result = evaluate_drained_state(
                store, output_dir=output_dir, pr_ref=str(pr.number)
            )
            result = {
                "status": STATUS_COMPLETED_NO_COMMENTS,
                "reason": "copilot_generated_no_comments",
                "cycle": state.get("cycle"),
                "pending_review_id": state.get("pending_review_id"),
                "timing": {
                    "stage2_max_wait_seconds": stage2_max_wait_seconds,
                    "elapsed_seconds": int(now - start),
                    "run_attempts": run_attempts,
                    "timeout_retries": timeout_retries,
                },
                "drain_guard": drained_result,
            }
            if drained_exit != 0:
                result["status"] = STATUS_BLOCKED_UNADDRESSED
                result["reason"] = "drain_guard_failed_after_terminal_review"
                store.append_event("stage2_loop_blocked_unaddressed", result)
            else:
                store.append_event("stage2_loop_completed_no_comments", result)
            attach_resume_command(
                result,
                state=state,
                output_dir=output_dir,
                pr_number=pr.number,
                stage2_max_wait_seconds=stage2_max_wait_seconds,
            )
            print(render_json(result))
            return drained_exit

        if status == STATUS_TIMEOUT:
            timeout_reason = state.get("last_timeout_reason")
            if timeout_reason == TIMEOUT_REASON_STAGE2_MAX_WAIT_REACHED:
                result = {
                    "status": STATUS_TIMEOUT,
                    "reason": TIMEOUT_REASON_STAGE2_MAX_WAIT_REACHED,
                    "message": "state is already terminal due to Stage 2 max-wait timeout",
                    "cycle": state.get("cycle"),
                    "timing": {
                        "stage2_max_wait_seconds": stage2_max_wait_seconds,
                        "elapsed_seconds": int(now - start),
                        "run_attempts": run_attempts,
                        "timeout_retries": timeout_retries,
                    },
                }
                attach_resume_command(
                    result,
                    state=state,
                    output_dir=output_dir,
                    pr_number=pr.number,
                    stage2_max_wait_seconds=stage2_max_wait_seconds,
                )
                store.append_event("stage2_loop_already_terminal_timeout", result)
                print(render_json(result))
                return EXIT_STAGE2_MAX_WAIT_REACHED

            state["status"] = transition_status(
                status, EVENT_STAGE2_RETRY_AFTER_CYCLE_TIMEOUT
            )
            state["last_timeout_reason"] = None
            store.save(state)
            timeout_retries += 1
            store.append_event(
                "stage2_loop_retry_after_cycle_timeout",
                {
                    "cycle": state["cycle"],
                    "timeout_retries": timeout_retries,
                    "remaining_seconds": remaining_seconds,
                    "timeout_reason": timeout_reason,
                },
            )
            continue

        if remaining_seconds <= 0:
            state["status"] = transition_status(status, EVENT_STAGE2_MAX_WAIT_REACHED)
            state["last_timeout_reason"] = TIMEOUT_REASON_STAGE2_MAX_WAIT_REACHED
            store.save(state)
            context_docs = update_context_documents(
                output_dir,
                state=state,
                pr=pr,
                phase=STATUS_TIMEOUT,
            )
            result = {
                "status": STATUS_TIMEOUT,
                "reason": "stage2_max_wait_reached",
                "timeout_reason": state["last_timeout_reason"],
                "cycle": state.get("cycle"),
                "timing": {
                    "stage2_max_wait_seconds": stage2_max_wait_seconds,
                    "elapsed_seconds": int(now - start),
                    "run_attempts": run_attempts,
                    "timeout_retries": timeout_retries,
                },
                "context_docs": context_docs,
            }
            attach_resume_command(
                result,
                state=state,
                output_dir=output_dir,
                pr_number=pr.number,
                stage2_max_wait_seconds=stage2_max_wait_seconds,
            )
            store.append_event("stage2_loop_timeout", result)
            print(render_json(result))
            return EXIT_STAGE2_MAX_WAIT_REACHED

        cycle_wait_seconds = min(max_wait_seconds, max(1, remaining_seconds))
        cycle_initial_sleep_seconds = (
            0 if run_attempts == 0 else initial_sleep_seconds
        )
        store.append_event(
            "stage2_loop_poll_cycle_started",
            {
                "cycle": state["cycle"],
                "run_attempt": run_attempts + 1,
                "cycle_wait_seconds": cycle_wait_seconds,
                "cycle_initial_sleep_seconds": cycle_initial_sleep_seconds,
                "remaining_seconds": remaining_seconds,
            },
        )
        run_attempts += 1
        exit_code = run_cycle(
            client,
            store,
            pr=pr,
            output_dir=output_dir,
            monitor_file=monitor_file,
            initial_sleep_seconds=cycle_initial_sleep_seconds,
            poll_interval_seconds=poll_interval_seconds,
            max_wait_seconds=cycle_wait_seconds,
        )
        if exit_code in {0, 3, 10}:
            continue
        return exit_code


def finalize_cycle(
    client: GhClient,
    store: AutopilotStateStore,
    *,
    output_dir: Path,
    pr: GhPrRef,
    request_reviewer: bool,
) -> int:
    state = store.load()
    ensure_state_pr_matches(state, pr)
    if state["status"] not in {STATUS_AWAITING_ADDRESS, STATUS_AWAITING_TRIAGE}:
        raise ValueError(
            f"finalize-cycle requires state {STATUS_AWAITING_ADDRESS} or {STATUS_AWAITING_TRIAGE}; got {state['status']}"
        )
    pending_review_id = state.get("pending_review_id")
    if not pending_review_id:
        raise ValueError("state is missing pending_review_id")
    finalize_artifacts = validate_finalize_artifacts(output_dir, state=state)

    if request_reviewer:
        client.re_request_copilot(pr.number)
        event_name = "cycle_finalized_and_rerequested"
        transition_event = EVENT_FINALIZE_WITH_REVIEWER_REQUEST
    else:
        event_name = "cycle_finalized_without_rerequest"
        transition_event = EVENT_FINALIZE_WITHOUT_REVIEWER_REQUEST

    state["last_processed_review_id"] = pending_review_id
    state["last_processed_review_submitted_at"] = state.get(
        "pending_review_submitted_at"
    )
    state["pending_review_id"] = None
    state["pending_review_submitted_at"] = None
    state["cycle"] = int(state["cycle"]) + 1
    state["status"] = transition_status(state["status"], transition_event)
    state["last_timeout_reason"] = None
    store.save(state)
    context_docs = update_context_documents(
        output_dir,
        state=state,
        pr=pr,
        phase=PHASE_FINALIZED,
        artifacts={
            "cycle_json": finalize_artifacts["cycle_json"],
        },
    )
    store.append_event(
        event_name,
        {
            "cycle": state["cycle"],
            "last_processed_review_id": state["last_processed_review_id"],
            "requested_reviewer": request_reviewer,
            "total_threads": finalize_artifacts["total_threads"],
            "total_comments": finalize_artifacts["total_comments"],
            "eligible_threads": finalize_artifacts["eligible_threads"],
            "eligible_comments": finalize_artifacts["eligible_comments"],
            "actionable_threads": finalize_artifacts["actionable_threads"],
            "non_actionable_threads": finalize_artifacts["non_actionable_threads"],
            "action_comments": finalize_artifacts["action_comments"],
            "no_action_comments": finalize_artifacts["no_action_comments"],
            "comment_statuses": finalize_artifacts["comment_statuses"],
        },
    )
    result = attach_resume_command(
        {
            "status": state["status"],
            "cycle": state["cycle"],
            "last_processed_review_id": state["last_processed_review_id"],
            "requested_reviewer": request_reviewer,
            "comment_statuses_recorded": len(finalize_artifacts["comment_statuses"]),
            "context_docs": context_docs,
        },
        state=state,
        output_dir=output_dir,
        pr_number=pr.number,
    )
    print(
        render_json(result)
    )
    return 0


def print_status(store: AutopilotStateStore, *, output_dir: Path) -> int:
    state = store.load()
    result = {
        "state_file": str(store.state_file),
        "events_file": str(store.events_file),
        "context_docs": {
            name: str(path) for name, path in context_doc_paths(output_dir).items()
        },
        "state": state,
    }
    pr_number = extract_pr_number(state)
    if pr_number is not None:
        attach_resume_command(
            result,
            state=state,
            output_dir=output_dir,
            pr_number=pr_number,
        )
    print(render_json(result))
    return 0


def evaluate_drained_state(
    store: AutopilotStateStore, *, output_dir: Path, pr_ref: str | None
) -> tuple[int, dict[str, Any]]:
    state = store.load()
    state_status = state.get("status")
    pending_cycle = state_status in {STATUS_AWAITING_ADDRESS, STATUS_AWAITING_TRIAGE}

    cycle_path = default_cycle_file(output_dir)
    cycle_summary: dict[str, Any] = {
        "cycle_json": str(cycle_path),
        "exists": cycle_path.exists(),
    }
    if cycle_path.exists():
        try:
            cycle_payload = load_required_json(cycle_path, label="cycle")
            coverage = summarize_feedback_coverage(cycle_payload)
            cycle_summary["total_threads"] = coverage["total_threads"]
            cycle_summary["total_comments"] = coverage["total_comments"]
            cycle_summary["eligible_threads"] = coverage["eligible_threads"]
            cycle_summary["eligible_comments"] = coverage["eligible_comments"]
            review = cycle_payload.get("copilot_review")
            if isinstance(review, dict):
                cycle_summary["review_id"] = review.get("id")
        except Exception as exc:  # pragma: no cover - defensive reporting only
            cycle_summary["error"] = str(exc)

    result: dict[str, Any] = {
        "state_file": str(store.state_file),
        "events_file": str(store.events_file),
        "status": "drained",
        "cycle": state.get("cycle"),
        "state_status": state_status,
        "pending_review_id": state.get("pending_review_id"),
        "cycle_artifact": cycle_summary,
        "pr": state.get("pr"),
    }
    if pr_ref:
        result["requested_pr"] = pr_ref
    pr_number = extract_pr_number(state)
    if pr_number is not None:
        attach_resume_command(
            result,
            state=state,
            output_dir=output_dir,
            pr_number=pr_number,
        )

    if pending_cycle:
        result["status"] = STATUS_BLOCKED_UNADDRESSED
        result["reason"] = (
            "state is awaiting_address/awaiting_triage; Stage 3 must complete before stop"
        )
        return EXIT_BLOCKED_UNADDRESSED, result

    result["reason"] = "no address-required cycle is currently pending"
    return 0, result


def command_assert_drained(
    store: AutopilotStateStore, *, output_dir: Path, pr_ref: str | None
) -> int:
    exit_code, result = evaluate_drained_state(
        store, output_dir=output_dir, pr_ref=pr_ref
    )
    print(render_json(result))
    return exit_code


def simulate_fsm_transitions(start_status: str, events: list[str]) -> dict[str, Any]:
    if start_status not in SIMULATION_START_STATUSES:
        raise ValueError(
            f"unsupported start status `{start_status}`; expected one of: "
            + ", ".join(SIMULATION_START_STATUSES)
        )
    if not events:
        raise ValueError("simulate-fsm requires at least one --event")

    current_status = start_status
    transitions: list[dict[str, Any]] = []
    for step, event in enumerate(events, start=1):
        if event not in SIMULATION_EVENTS:
            raise ValueError(
                f"unsupported event `{event}` at step {step}; expected one of: "
                + ", ".join(SIMULATION_EVENTS)
            )
        try:
            next_status = transition_status(current_status, event)
        except ValueError as exc:
            raise ValueError(
                f"simulate-fsm step {step} failed: status={current_status}, event={event}"
            ) from exc

        transitions.append(
            {
                "step": step,
                "from_status": current_status,
                "event": event,
                "to_status": next_status,
            }
        )
        current_status = next_status

    return {
        "status": "simulated",
        "start_status": start_status,
        "events": events,
        "transitions": transitions,
        "final_status": current_status,
        "is_terminal": current_status in TERMINAL_STATUSES,
    }


def command_simulate_fsm(*, start_status: str, events: list[str]) -> int:
    result = simulate_fsm_transitions(start_status, events)
    print(render_json(result))
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Standalone GH Autopilot loop engine.")
    parser.add_argument("--repo", default=".", help="Local repository path.")
    parser.add_argument(
        "--pr",
        default=None,
        help="PR number or URL. If omitted, resolve from current branch.",
    )
    parser.add_argument(
        "--output-dir",
        default=DEFAULT_OUTPUT_DIR,
        help="Directory for state and cycle artifacts.",
    )
    parser.add_argument(
        "--state-file",
        default=None,
        help="Override state file path (default: <output-dir>/state.json).",
    )
    parser.add_argument(
        "--events-file",
        default=None,
        help="Override events file path (default: <output-dir>/events.jsonl).",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    init_parser = subparsers.add_parser("init", help="Initialize loop state.")
    init_parser.add_argument(
        "--initial-sleep-seconds",
        type=int,
        default=300,
        help="Initial sleep before first review poll.",
    )
    init_parser.add_argument(
        "--poll-interval-seconds",
        type=int,
        default=45,
        help="Polling interval after initial sleep.",
    )
    init_parser.add_argument(
        "--cycle-max-wait-seconds",
        dest="max_wait_seconds",
        type=int,
        default=2400,
        help="Maximum per-cycle wait before timeout.",
    )
    init_parser.add_argument(
        "--force",
        action="store_true",
        help="Reset existing state file.",
    )

    cycle_parser = subparsers.add_parser(
        "run-cycle",
        help="Wait for a new review and export artifacts for one cycle.",
    )
    cycle_parser.add_argument(
        "--initial-sleep-seconds",
        type=int,
        default=300,
        help="Initial sleep before first review poll.",
    )
    cycle_parser.add_argument(
        "--poll-interval-seconds",
        type=int,
        default=45,
        help="Polling interval after initial sleep.",
    )
    cycle_parser.add_argument(
        "--cycle-max-wait-seconds",
        dest="max_wait_seconds",
        type=int,
        default=2400,
        help="Maximum per-cycle wait before timeout.",
    )
    cycle_parser.add_argument(
        "--monitor-file",
        default=None,
        help=(
            "Legacy option retained for compatibility; monitor snapshots are recorded in "
            "state.last_wait and event payloads."
        ),
    )

    stage2_parser = subparsers.add_parser(
        "run-stage2-loop",
        help=(
            "Run Stage 2 monitor loop with automatic retries after per-cycle timeout "
            "until action is required, no-comments terminal, or Stage 2 max wait is reached."
        ),
    )
    stage2_parser.add_argument(
        "--initial-sleep-seconds",
        type=int,
        default=300,
        help="Initial sleep before first review poll.",
    )
    stage2_parser.add_argument(
        "--poll-interval-seconds",
        type=int,
        default=45,
        help="Polling interval after initial sleep.",
    )
    stage2_parser.add_argument(
        "--cycle-max-wait-seconds",
        dest="max_wait_seconds",
        type=int,
        default=2400,
        help="Maximum per-cycle wait before timeout.",
    )
    stage2_parser.add_argument(
        "--stage2-max-wait-seconds",
        type=int,
        default=DEFAULT_STAGE2_MAX_WAIT_SECONDS,
        help=(
            "Maximum total Stage 2 wall-clock wait across repeated cycle retries "
            "before stopping."
        ),
    )
    stage2_parser.add_argument(
        "--monitor-file",
        default=None,
        help=(
            "Legacy option retained for compatibility; monitor snapshots are recorded in "
            "state.last_wait and event payloads."
        ),
    )

    finalize_parser = subparsers.add_parser(
        "finalize-cycle",
        help="Mark current cycle addressed and optionally re-request reviewer.",
    )
    finalize_parser.add_argument(
        "--skip-reviewer-request",
        action="store_true",
        help="Finalize cycle without remove/add reviewer calls.",
    )

    subparsers.add_parser("status", help="Print current state JSON.")
    subparsers.add_parser(
        "assert-drained",
        help=(
            "Fail when an address-required cycle is pending; "
            "use before declaring loop completion."
        ),
    )

    simulate_parser = subparsers.add_parser(
        "simulate-fsm",
        help="Deterministically simulate FSM status transitions with explicit events.",
    )
    simulate_parser.add_argument(
        "--start-status",
        default=STATUS_INITIALIZED,
        choices=SIMULATION_START_STATUSES,
        help="Initial status before applying transitions.",
    )
    simulate_parser.add_argument(
        "--event",
        dest="events",
        action="append",
        required=True,
        choices=SIMULATION_EVENTS,
        help="Transition event to apply; repeat for each step.",
    )
    return parser.parse_args()


def command_init(
    client: GhClient,
    store: AutopilotStateStore,
    *,
    output_dir: Path,
    pr_ref: str | None,
    initial_sleep_seconds: int,
    poll_interval_seconds: int,
    max_wait_seconds: int,
    force: bool,
) -> int:
    validate_monitor_args(
        initial_sleep_seconds, poll_interval_seconds, max_wait_seconds
    )
    client.ensure_auth()
    pr = client.resolve_pr(pr_ref)
    state = init_state(
        store,
        pr=pr,
        initial_sleep_seconds=initial_sleep_seconds,
        poll_interval_seconds=poll_interval_seconds,
        max_wait_seconds=max_wait_seconds,
        force=force,
    )
    context_docs = update_context_documents(
        output_dir,
        state=state,
        pr=pr,
        phase=STATUS_INITIALIZED,
    )
    result = attach_resume_command(
        {
            "status": "initialized",
            "state_file": str(store.state_file),
            "events_file": str(store.events_file),
            "context_docs": context_docs,
            "state": state,
        },
        state=state,
        output_dir=output_dir,
        pr_number=pr.number,
    )
    print(
        render_json(result)
    )
    return 0


def command_run_cycle(
    client: GhClient,
    store: AutopilotStateStore,
    *,
    output_dir: Path,
    pr_ref: str | None,
    monitor_file: Path,
    initial_sleep_seconds: int,
    poll_interval_seconds: int,
    max_wait_seconds: int,
) -> int:
    validate_monitor_args(
        initial_sleep_seconds, poll_interval_seconds, max_wait_seconds
    )
    client.ensure_auth()
    pr = client.resolve_pr(pr_ref)
    return run_cycle(
        client,
        store,
        pr=pr,
        output_dir=output_dir,
        monitor_file=monitor_file,
        initial_sleep_seconds=initial_sleep_seconds,
        poll_interval_seconds=poll_interval_seconds,
        max_wait_seconds=max_wait_seconds,
    )


def command_run_stage2_loop(
    client: GhClient,
    store: AutopilotStateStore,
    *,
    output_dir: Path,
    pr_ref: str | None,
    monitor_file: Path,
    initial_sleep_seconds: int,
    poll_interval_seconds: int,
    max_wait_seconds: int,
    stage2_max_wait_seconds: int,
) -> int:
    validate_monitor_args(
        initial_sleep_seconds, poll_interval_seconds, max_wait_seconds
    )
    if stage2_max_wait_seconds <= 0:
        raise ValueError("--stage2-max-wait-seconds must be > 0")
    client.ensure_auth()
    pr = client.resolve_pr(pr_ref)
    return run_stage2_loop(
        client,
        store,
        pr=pr,
        output_dir=output_dir,
        monitor_file=monitor_file,
        initial_sleep_seconds=initial_sleep_seconds,
        poll_interval_seconds=poll_interval_seconds,
        max_wait_seconds=max_wait_seconds,
        stage2_max_wait_seconds=stage2_max_wait_seconds,
    )


def command_finalize_cycle(
    client: GhClient,
    store: AutopilotStateStore,
    *,
    output_dir: Path,
    pr_ref: str | None,
    skip_reviewer_request: bool,
) -> int:
    client.ensure_auth()
    pr = client.resolve_pr(pr_ref)
    return finalize_cycle(
        client,
        store,
        output_dir=output_dir,
        pr=pr,
        request_reviewer=not skip_reviewer_request,
    )


def command_status(store: AutopilotStateStore, *, output_dir: Path) -> int:
    return print_status(store, output_dir=output_dir)


def main() -> int:
    try:
        args = parse_args()
        repo_path = Path(args.repo).resolve()
        output_dir = Path(args.output_dir).resolve()
        state_file = (
            Path(args.state_file).resolve()
            if args.state_file
            else default_state_file(output_dir)
        )
        events_file = (
            Path(args.events_file).resolve()
            if args.events_file
            else default_events_file(output_dir)
        )

        client = GhClient(repo_path=repo_path)
        store = AutopilotStateStore(state_file=state_file, events_file=events_file)

        if args.command == "init":
            return command_init(
                client,
                store,
                output_dir=output_dir,
                pr_ref=args.pr,
                initial_sleep_seconds=args.initial_sleep_seconds,
                poll_interval_seconds=args.poll_interval_seconds,
                max_wait_seconds=args.max_wait_seconds,
                force=args.force,
            )
        if args.command == "run-cycle":
            monitor_file = (
                Path(args.monitor_file).resolve()
                if args.monitor_file
                else default_monitor_file(output_dir)
            )
            return command_run_cycle(
                client,
                store,
                output_dir=output_dir,
                pr_ref=args.pr,
                monitor_file=monitor_file,
                initial_sleep_seconds=args.initial_sleep_seconds,
                poll_interval_seconds=args.poll_interval_seconds,
                max_wait_seconds=args.max_wait_seconds,
            )
        if args.command == "run-stage2-loop":
            monitor_file = (
                Path(args.monitor_file).resolve()
                if args.monitor_file
                else default_monitor_file(output_dir)
            )
            return command_run_stage2_loop(
                client,
                store,
                output_dir=output_dir,
                pr_ref=args.pr,
                monitor_file=monitor_file,
                initial_sleep_seconds=args.initial_sleep_seconds,
                poll_interval_seconds=args.poll_interval_seconds,
                max_wait_seconds=args.max_wait_seconds,
                stage2_max_wait_seconds=args.stage2_max_wait_seconds,
            )
        if args.command == "finalize-cycle":
            return command_finalize_cycle(
                client,
                store,
                output_dir=output_dir,
                pr_ref=args.pr,
                skip_reviewer_request=args.skip_reviewer_request,
            )
        if args.command == "status":
            return command_status(store, output_dir=output_dir)
        if args.command == "assert-drained":
            return command_assert_drained(
                store,
                output_dir=output_dir,
                pr_ref=args.pr,
            )
        if args.command == "simulate-fsm":
            return command_simulate_fsm(
                start_status=args.start_status,
                events=args.events,
            )

        raise ValueError(f"unsupported command: {args.command}")
    except Exception as exc:  # pragma: no cover - defensive CLI boundary
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
