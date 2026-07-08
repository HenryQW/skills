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


def normalize_child(child: dict[str, Any], status: str | None) -> dict[str, Any]:
    child = dict(child)
    child["issue"] = child_issue(child)
    if status:
        child["status"] = status
    return child


def extend_unique(existing: list[Any], values: list[Any]) -> list[Any]:
    result = list(existing)
    for value in values:
        if value not in result:
            result.append(value)
    return result


def update_validation_plan(manifest: dict[str, Any], child: dict[str, Any]) -> None:
    plan = manifest.setdefault("validation_plan", {"touched_files": [], "checks": [], "final_checks": [], "known_skips": []})
    plan["touched_files"] = extend_unique(plan.get("touched_files", []), child.get("changed_files", []))
    plan["checks"] = extend_unique(plan.get("checks", []), child.get("checks", []))
    plan["known_skips"] = extend_unique(plan.get("known_skips", []), child.get("known_skips", []))


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


def set_child(path: Path, child: dict[str, Any], status: str | None) -> dict[str, Any]:
    manifest = load_manifest(path)
    child = normalize_child(child, status)
    missing = REQUIRED_CHILD - set(child)
    if missing:
        raise SystemExit("child payload missing field(s): " + ", ".join(sorted(missing)))
    errors = pending_review_errors(child, "child payload")
    if errors:
        raise SystemExit("\n".join(errors))
    children = [item for item in manifest.get("children", []) if item.get("issue") != child["issue"]]
    children.append(child)
    manifest["children"] = sorted(children, key=lambda item: int(str(item["issue"]).lstrip("#")))
    update_validation_plan(manifest, child)
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
        if child.get("review") not in {"PASS", "PENDING_REVIEW", "FAIL"}:
            errors.append(f"children[{index}] review must be PASS, PENDING_REVIEW, or FAIL")
        errors.extend(pending_review_errors(child, f"children[{index}]"))
    return errors


def self_test() -> int:
    with tempfile.TemporaryDirectory() as raw_tmp:
        old_cwd = os.getcwd()
        try:
            os.chdir(raw_tmp)
            path = DEFAULT_MANIFEST
            init_manifest(path, "#123", "shipyard-123", "main")
            child = {
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
            set_child(path, child, "merged")
            missing = dict(child)
            missing.pop("changed_files")
            try:
                set_child(path, missing, "merged")
            except SystemExit as exc:
                assert "changed_files" in str(exc)
            else:
                raise AssertionError("expected missing changed_files to fail")
            try:
                set_child(path, child, None)
            except SystemExit as exc:
                assert "status" in str(exc)
            else:
                raise AssertionError("expected missing status to fail")
            pending = dict(child, issue="#232", review="PENDING_REVIEW")
            try:
                set_child(path, pending, "pending_review")
            except SystemExit as exc:
                assert "pending_review" in str(exc)
            else:
                raise AssertionError("expected missing pending_review evidence to fail")
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
            set_child(path, pending, "pending_review")
            pending["pending_review"]["review_id"] = ""
            try:
                set_child(path, pending, "pending_review")
            except SystemExit as exc:
                assert "review_id" in str(exc)
            else:
                raise AssertionError("expected empty pending_review evidence to fail")
            set_review(path, {"scope": "shipyard", "status": "PASS"})
            set_pr(path, "https://github.com/org/repo/pull/1")
            manifest = load_manifest(path)
            errors = validate_manifest(manifest)
            assert errors == []
            progress = json.loads((path.parent / "progress.md").read_text(encoding="utf-8"))
            assert progress["artifacts"]["manifest"] == os.fspath(path.resolve())
            assert manifest["children"][0]["status"] == "merged"
            assert manifest["validation_plan"]["touched_files"] == ["README.md"]
            assert manifest["validation_plan"]["checks"] == ["python3 scripts/validate.py -> passed"]
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

    child = subparsers.add_parser("set-child")
    child.add_argument("--json")
    child.add_argument("--file")
    child.add_argument("--status")

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
    elif args.command == "set-child":
        set_child(path, read_json_arg(args.json, args.file), args.status)
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
