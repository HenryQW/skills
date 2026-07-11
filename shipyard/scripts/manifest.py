#!/usr/bin/env python3
"""Maintain the shipyard run manifest."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


VERSION = 1
DEFAULT_MANIFEST = Path(".context/shipyard-manifest.json")
REQUIRED_TOP_LEVEL = {
    "version",
    "parent_issue",
    "integration_branch",
    "children",
    "validation_plan",
    "review_gate",
    "blockers",
    "pr_url",
}
REQUIRED_CHILD = {
    "issue",
    "branch",
    "worktree",
    "base_ref",
    "base_sha",
    "commit",
    "head_sha",
    "changed_files",
    "diff_stat",
    "verification",
    "review",
    "checks",
    "known_skips",
    "status",
}
REQUIRED_HANDOFF = REQUIRED_CHILD - {"status"}
REQUIRED_PENDING_REVIEW = {
    "review_id",
    "branch",
    "local_head_sha",
    "upstream_sha",
    "base_ref",
    "base_sha",
    "poll_after_utc",
    "progress_path",
}
ALLOWED_CHILD_STATUS = {"returned", "needs_fix", "pending_review", "merged"}
REVIEW_STATUS = {
    "PASS": {"returned", "merged"},
    "PENDING_REVIEW": {"pending_review"},
    "FAIL": {"needs_fix"},
}
HANDOFF_TRANSITIONS = {
    "pending_review": {"returned", "needs_fix"},
    "needs_fix": {"pending_review", "returned"},
}


def now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def normalize_issue(value: str) -> str:
    match = re.search(r"#?([1-9][0-9]*)$", value.strip())
    if not match:
        raise SystemExit(f"issue must look like #123: {value}")
    return f"#{match.group(1)}"


def load_manifest(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise SystemExit(f"manifest not found: {path}") from None


def save_manifest(path: Path, manifest: dict[str, Any]) -> None:
    manifest["updated_at"] = now_utc()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def read_json_arg(raw: str | None, file_path: str | None) -> dict[str, Any]:
    if bool(raw) == bool(file_path):
        raise SystemExit("pass exactly one of --json or --file")
    text = Path(file_path).read_text(encoding="utf-8") if file_path else raw
    value = json.loads(text or "{}")
    if not isinstance(value, dict):
        raise SystemExit("JSON payload must be an object")
    return value


def progress_pointer(manifest_path: Path, manifest: dict[str, Any]) -> dict[str, Any]:
    return {
        "goal": f"shipyard {manifest['parent_issue']}",
        "current_step": manifest.get("current_step", "use shipyard manifest"),
        "artifacts": {"manifest": os.fspath(manifest_path.resolve())},
        "blockers": manifest.get("blockers", []),
        "validation": manifest.get("validation_plan", {}).get("checks", []),
    }


def write_progress_pointer(manifest_path: Path, manifest: dict[str, Any]) -> None:
    progress = manifest_path.parent / "progress.md"
    progress.write_text(json.dumps(progress_pointer(manifest_path, manifest), indent=2, sort_keys=True) + "\n", encoding="utf-8")


def init_manifest(path: Path, parent_issue: str, integration_branch: str, base_branch: str | None) -> dict[str, Any]:
    manifest = {
        "version": VERSION,
        "parent_issue": normalize_issue(parent_issue),
        "integration_branch": integration_branch,
        "base_branch": base_branch,
        "current_step": "inspect runnable children",
        "children": [],
        "validation_plan": {
            "touched_files": [],
            "checks": [],
            "final_checks": [],
            "known_skips": [],
        },
        "review_gate": {
            "latest": None,
            "events": [],
        },
        "blockers": [],
        "pr_url": None,
        "created_at": now_utc(),
        "updated_at": now_utc(),
    }
    save_manifest(path, manifest)
    write_progress_pointer(path, manifest)
    return manifest


def child_issue(child: dict[str, Any]) -> str:
    value = child.get("issue")
    if isinstance(value, str):
        return normalize_issue(value)
    raise SystemExit("child payload requires issue")


def normalize_child(child: dict[str, Any]) -> dict[str, Any]:
    child = dict(child)
    child["issue"] = child_issue(child)
    return child


def extend_unique(existing: list[Any], values: list[Any]) -> list[Any]:
    result = list(existing)
    for value in values:
        if value not in result:
            result.append(value)
    return result


def rebuild_validation_plan(manifest: dict[str, Any]) -> None:
    existing = manifest.get("validation_plan", {})
    plan = {
        "touched_files": [],
        "checks": [],
        "final_checks": existing.get("final_checks", []),
        "known_skips": [],
    }
    for child in manifest.get("children", []):
        plan["touched_files"] = extend_unique(plan["touched_files"], child.get("changed_files", []))
        plan["checks"] = extend_unique(plan["checks"], child.get("checks", []))
        plan["known_skips"] = extend_unique(plan["known_skips"], child.get("known_skips", []))
    manifest["validation_plan"] = plan


def status_errors(child: dict[str, Any], prefix: str) -> list[str]:
    if child.get("status") in ALLOWED_CHILD_STATUS:
        return []
    return [f"{prefix} status must be one of: " + ", ".join(sorted(ALLOWED_CHILD_STATUS))]


def review_status_errors(child: dict[str, Any], prefix: str) -> list[str]:
    allowed = REVIEW_STATUS.get(child.get("review"))
    if not allowed:
        return [f"{prefix} review must be PASS, PENDING_REVIEW, or FAIL"]
    if child.get("status") in allowed:
        return []
    return [f"{prefix} status {child.get('status')} does not match review {child.get('review')}"]


def failed_review_errors(child: dict[str, Any], prefix: str) -> list[str]:
    if child.get("review") != "FAIL":
        return []
    value = child.get("needs_child_fix")
    if not isinstance(value, str) or not re.fullmatch(r"#[1-9][0-9]*", value.strip()):
        return [f"{prefix} review FAIL requires needs_child_fix"]
    return []


def verification_errors(child: dict[str, Any], prefix: str) -> list[str]:
    value = child.get("verification")
    if isinstance(value, str) and (value.startswith("pass:") or value.startswith("skip:")):
        return []
    return [f"{prefix} verification must start with pass: or skip:"]


def pending_review_errors(child: dict[str, Any], prefix: str) -> list[str]:
    if child.get("review") != "PENDING_REVIEW":
        return []
    pending = child.get("pending_review")
    if not isinstance(pending, dict):
        return [f"{prefix} requires pending_review evidence"]
    missing = [
        field
        for field in sorted(REQUIRED_PENDING_REVIEW)
        if not isinstance(pending.get(field), str) or not pending[field].strip()
    ]
    return [f"{prefix} pending_review missing/empty field: {field}" for field in missing]


def handoff_status(child: dict[str, Any]) -> str:
    return {
        "PASS": "returned",
        "PENDING_REVIEW": "pending_review",
        "FAIL": "needs_fix",
    }.get(child.get("review"), "")


def handoff_data(child: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in child.items() if key != "status"}


def child_payload_errors(child: dict[str, Any]) -> list[str]:
    return (
        review_status_errors(child, "child payload")
        + verification_errors(child, "child payload")
        + failed_review_errors(child, "child payload")
        + pending_review_errors(child, "child payload")
    )


def ingest_child(path: Path, child: dict[str, Any]) -> dict[str, Any]:
    manifest = load_manifest(path)
    child = normalize_child(child)
    missing = REQUIRED_HANDOFF - set(child)
    if missing:
        raise SystemExit("child payload missing field(s): " + ", ".join(sorted(missing)))
    child["status"] = handoff_status(child)
    errors = child_payload_errors(child)
    if errors:
        raise SystemExit("\n".join(errors))
    existing = next((item for item in manifest.get("children", []) if item.get("issue") == child["issue"]), None)
    if existing:
        if handoff_data(existing) == handoff_data(child):
            return manifest
        allowed = HANDOFF_TRANSITIONS.get(existing.get("status"), set())
        if child["status"] not in allowed:
            raise SystemExit(f"child {child['issue']} cannot transition from {existing.get('status')} to {child['status']}")
    children = [item for item in manifest.get("children", []) if item.get("issue") != child["issue"]]
    children.append(child)
    manifest["children"] = sorted(children, key=lambda item: int(str(item["issue"]).lstrip("#")))
    rebuild_validation_plan(manifest)
    errors = validate_manifest(manifest)
    if errors:
        raise SystemExit("\n".join(errors))
    save_manifest(path, manifest)
    write_progress_pointer(path, manifest)
    return manifest


def merge_child(path: Path, issue: str, commit: str) -> dict[str, Any]:
    manifest = load_manifest(path)
    normalized_issue = normalize_issue(issue)
    existing = next((item for item in manifest.get("children", []) if item.get("issue") == normalized_issue), None)
    if not existing:
        raise SystemExit(f"child {normalized_issue} has no ingested handoff")
    if existing.get("commit") != commit:
        raise SystemExit(f"child {normalized_issue} commit does not match ingested handoff")
    if existing.get("status") == "merged":
        return manifest
    if existing.get("status") != "returned":
        raise SystemExit(f"child {normalized_issue} cannot transition from {existing.get('status')} to merged")
    existing["status"] = "merged"
    errors = validate_manifest(manifest)
    if errors:
        raise SystemExit("\n".join(errors))
    save_manifest(path, manifest)
    write_progress_pointer(path, manifest)
    return manifest


def set_review(path: Path, event: dict[str, Any]) -> dict[str, Any]:
    manifest = load_manifest(path)
    event = dict(event)
    event.setdefault("recorded_at", now_utc())
    review_gate = manifest.setdefault("review_gate", {"latest": None, "events": []})
    events = review_gate.setdefault("events", [])
    if not isinstance(events, list):
        raise SystemExit("review_gate.events must be a list")
    events.append(event)
    review_gate["latest"] = event
    save_manifest(path, manifest)
    write_progress_pointer(path, manifest)
    return manifest


def set_pr(path: Path, url: str) -> dict[str, Any]:
    manifest = load_manifest(path)
    manifest["pr_url"] = url
    manifest["current_step"] = "pull request created"
    save_manifest(path, manifest)
    write_progress_pointer(path, manifest)
    return manifest


def validate_manifest(manifest: dict[str, Any]) -> list[str]:
    errors = [f"missing top-level field: {field}" for field in sorted(REQUIRED_TOP_LEVEL - set(manifest))]
    if manifest.get("version") != VERSION:
        errors.append(f"unsupported version: {manifest.get('version')}")
    if not isinstance(manifest.get("children"), list):
        errors.append("children must be a list")
        return errors
    for index, child in enumerate(manifest["children"]):
        missing = REQUIRED_CHILD - set(child)
        errors.extend(f"children[{index}] missing field: {field}" for field in sorted(missing))
        errors.extend(status_errors(child, f"children[{index}]"))
        errors.extend(review_status_errors(child, f"children[{index}]"))
        errors.extend(verification_errors(child, f"children[{index}]"))
        errors.extend(failed_review_errors(child, f"children[{index}]"))
        errors.extend(pending_review_errors(child, f"children[{index}]"))
    return errors


def self_test() -> int:
    with tempfile.TemporaryDirectory() as raw_tmp:
        old_cwd = os.getcwd()
        try:
            os.chdir(raw_tmp)
            path = DEFAULT_MANIFEST
            init_manifest(path, "#123", "shipyard-123", "main")
            passed = {
                "issue": "#231",
                "branch": "issue-231",
                "worktree": "/tmp/child",
                "base_ref": "shipyard-123",
                "base_sha": "a" * 40,
                "head_sha": "b" * 40,
                "commit": "b" * 40,
                "changed_files": ["README.md"],
                "diff_stat": "README.md | 1 +",
                "verification": "pass:unit",
                "review": "PASS",
                "checks": ["python3 scripts/validate.py -> passed"],
                "known_skips": [],
            }
            ingest_child(path, passed)
            manifest = load_manifest(path)
            assert manifest["children"][0]["status"] == "returned"
            assert manifest["validation_plan"]["touched_files"] == ["README.md"]
            unchanged = path.read_text(encoding="utf-8")
            unchanged_progress = (path.parent / "progress.md").read_text(encoding="utf-8")
            ingest_child(path, passed)
            assert path.read_text(encoding="utf-8") == unchanged
            assert (path.parent / "progress.md").read_text(encoding="utf-8") == unchanged_progress
            conflicting = dict(passed, changed_files=["other.py"])
            try:
                ingest_child(path, conflicting)
            except SystemExit as exc:
                assert "cannot transition from returned to returned" in str(exc)
            else:
                raise AssertionError("expected conflicting repeat to fail")
            assert path.read_text(encoding="utf-8") == unchanged
            assert (path.parent / "progress.md").read_text(encoding="utf-8") == unchanged_progress
            try:
                merge_child(path, "#999", "b" * 40)
            except SystemExit as exc:
                assert "no ingested handoff" in str(exc)
            else:
                raise AssertionError("expected out-of-order merge to fail")
            assert path.read_text(encoding="utf-8") == unchanged
            merge_child(path, "#231", "b" * 40)
            merged = path.read_text(encoding="utf-8")
            merge_child(path, "#231", "b" * 40)
            assert path.read_text(encoding="utf-8") == merged
            try:
                merge_child(path, "#231", "c" * 40)
            except SystemExit as exc:
                assert "commit does not match" in str(exc)
            else:
                raise AssertionError("expected conflicting merge repeat to fail")
            assert path.read_text(encoding="utf-8") == merged

            pending = dict(passed, issue="#232", branch="issue-232", review="PENDING_REVIEW")
            before_pending = path.read_text(encoding="utf-8")
            try:
                ingest_child(path, pending)
            except SystemExit as exc:
                assert "pending_review" in str(exc)
            else:
                raise AssertionError("expected pending handoff without evidence to fail")
            assert path.read_text(encoding="utf-8") == before_pending
            pending["pending_review"] = {
                "review_id": "review-1",
                "branch": "issue-232",
                "local_head_sha": "b" * 40,
                "upstream_sha": "b" * 40,
                "base_ref": "shipyard-123",
                "base_sha": "a" * 40,
                "poll_after_utc": "2026-07-08T05:30:00Z",
                "progress_path": "/tmp/child/.context/progress.md",
            }
            ingest_child(path, pending)
            before_out_of_order = path.read_text(encoding="utf-8")
            try:
                merge_child(path, "#232", "b" * 40)
            except SystemExit as exc:
                assert "cannot transition from pending_review to merged" in str(exc)
            else:
                raise AssertionError("expected pending child merge to fail")
            assert path.read_text(encoding="utf-8") == before_out_of_order
            resumed = dict(passed, issue="#232", branch="issue-232")
            ingest_child(path, resumed)
            assert next(child for child in load_manifest(path)["children"] if child["issue"] == "#232")["status"] == "returned"

            failed = dict(passed, issue="#233", branch="issue-233", review="FAIL")
            before_failed = path.read_text(encoding="utf-8")
            try:
                ingest_child(path, failed)
            except SystemExit as exc:
                assert "needs_child_fix" in str(exc)
            else:
                raise AssertionError("expected failed handoff without evidence to fail")
            assert path.read_text(encoding="utf-8") == before_failed
            failed["needs_child_fix"] = "#231"
            ingest_child(path, failed)
            fixed = dict(passed, issue="#233", branch="issue-233")
            ingest_child(path, fixed)
            assert next(child for child in load_manifest(path)["children"] if child["issue"] == "#233")["status"] == "returned"

            invalid = dict(passed, issue="#234", verification="failed tests")
            before_invalid = path.read_text(encoding="utf-8")
            try:
                ingest_child(path, invalid)
            except SystemExit as exc:
                assert "verification" in str(exc)
            else:
                raise AssertionError("expected invalid handoff to fail")
            assert path.read_text(encoding="utf-8") == before_invalid

            set_review(path, {"scope": "shipyard", "status": "PASS"})
            set_pr(path, "https://github.com/org/repo/pull/1")
            manifest = load_manifest(path)
            errors = validate_manifest(manifest)
            assert errors == []
            progress = json.loads((path.parent / "progress.md").read_text(encoding="utf-8"))
            assert progress["artifacts"]["manifest"] == os.fspath(path.resolve())
            assert manifest["children"][0]["status"] == "merged"
            assert manifest["review_gate"]["latest"]["scope"] == "shipyard"
        finally:
            os.chdir(old_cwd)
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Maintain .context/shipyard-manifest.json")
    parser.add_argument("--manifest", default=os.fspath(DEFAULT_MANIFEST))
    parser.add_argument("--self-test", action="store_true")
    subparsers = parser.add_subparsers(dest="command")

    init = subparsers.add_parser("init")
    init.add_argument("parent_issue")
    init.add_argument("integration_branch")
    init.add_argument("--base-branch")

    child = subparsers.add_parser("ingest-child")
    child.add_argument("--json")
    child.add_argument("--file")

    merged_child = subparsers.add_parser("merge-child")
    merged_child.add_argument("issue")
    merged_child.add_argument("--commit", required=True)

    review = subparsers.add_parser("set-review")
    review.add_argument("--json")
    review.add_argument("--file")

    pr = subparsers.add_parser("set-pr")
    pr.add_argument("url")

    subparsers.add_parser("validate")

    args = parser.parse_args()
    path = Path(args.manifest)

    if args.self_test:
        return self_test()
    if args.command == "init":
        init_manifest(path, args.parent_issue, args.integration_branch, args.base_branch)
    elif args.command == "ingest-child":
        ingest_child(path, read_json_arg(args.json, args.file))
    elif args.command == "merge-child":
        merge_child(path, args.issue, args.commit)
    elif args.command == "set-review":
        set_review(path, read_json_arg(args.json, args.file))
    elif args.command == "set-pr":
        set_pr(path, args.url)
    elif args.command == "validate":
        errors = validate_manifest(load_manifest(path))
        if errors:
            print("\n".join(errors), file=sys.stderr)
            return 1
        print(f"manifest ok: {path}")
    else:
        parser.print_help()
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
