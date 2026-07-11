#!/usr/bin/env python3
"""Publish rendered issue plans with gh."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import tempfile
from pathlib import Path

from render_issue_plan import render
from render_issue_plan import ordered_issues
from render_issue_plan import self_test as render_self_test


def run(cmd: list[str]) -> str:
    return subprocess.check_output(cmd, text=True).strip()


def save(path: Path, data: dict[str, str]) -> None:
    path.write_text(json.dumps(data, indent=2) + "\n")


def publish(plan_path: Path, repo: str, labels: list[str], out: Path, resume: bool = False) -> dict[str, str]:
    plan_data = plan_path.read_bytes()
    plan = json.loads(plan_data)
    numbers_path = out / "numbers.json"
    state_path = out / "publish-state.json"
    expected_state = {"repo": repo, "plan_sha256": hashlib.sha256(plan_data).hexdigest()}
    checkpoint_exists = numbers_path.exists() or state_path.exists()
    if checkpoint_exists and not resume:
        raise SystemExit(f"{out} contains a publish checkpoint; pass --resume to continue without duplicating recorded issues")
    if resume and not checkpoint_exists:
        raise SystemExit(f"{out} has no publish checkpoint to resume")
    if resume and (not state_path.exists() or json.loads(state_path.read_text()) != expected_state):
        raise SystemExit(f"{state_path} does not match this plan and repository")
    numbers = json.loads(numbers_path.read_text()) if numbers_path.exists() else {}
    allowed = {issue["id"] for issue in plan["issues"]} | {"tracker"}
    if not isinstance(numbers, dict) or set(numbers) - allowed:
        raise SystemExit(f"{numbers_path} does not match this plan")
    if any(not isinstance(number, str) or not number.startswith("#") or not number[1:].isdigit() for number in numbers.values()):
        raise SystemExit(f"{numbers_path} contains invalid issue numbers")
    if "tracker" in numbers and not allowed - {"tracker"} <= set(numbers):
        raise SystemExit(f"{numbers_path} records the tracker before all children")

    render(plan_path, out, numbers_path if numbers else None, numbers.get("tracker"))
    if not state_path.exists():
        save(state_path, expected_state)
    label_args = [arg for label in labels for arg in ("--label", label)]

    for row in (out / "create-order.tsv").read_text().splitlines():
        issue_id, title, body_file = row.split("\t")
        if issue_id in numbers:
            continue
        url = run(["gh", "issue", "create", "--repo", repo, "--title", title, *label_args, "--body-file", body_file])
        numbers[issue_id] = f"#{url.rsplit('/', 1)[-1]}"
        save(numbers_path, numbers)

    render(plan_path, out, numbers_path, None)

    if "tracker" not in numbers:
        tracker_title = plan["tracker"]["title"]
        tracker_url = run(["gh", "issue", "create", "--repo", repo, "--title", tracker_title, *label_args, "--body-file", str(out / "00-tracker.md")])
        numbers["tracker"] = f"#{tracker_url.rsplit('/', 1)[-1]}"
        save(numbers_path, numbers)
    render(plan_path, out, numbers_path, numbers["tracker"])

    for row in (out / "create-order.tsv").read_text().splitlines():
        issue_id, _, body_file = row.split("\t")
        run(["gh", "issue", "edit", numbers[issue_id].lstrip("#"), "--repo", repo, "--body-file", body_file])
    return numbers


def execution_block(plan_path: Path, numbers: dict[str, str], repo: str, worktree: Path, numbers_path: Path) -> str:
    plan = json.loads(plan_path.read_text())
    children = [numbers[issue["id"]] for issue in ordered_issues(plan)]
    final_check = next(numbers[issue["id"]] for issue in plan["issues"] if issue.get("role") == "final_check")
    parent = numbers["tracker"]
    return "\n".join(
        [
            "execution:",
            f"parent_issue={parent}",
            f"child_issues={' '.join(children)}",
            f"final_check_issue={final_check}",
            f"numbers_json={numbers_path.resolve()}",
            f"shipyard_worktree={worktree}",
            f"shipyard_command=Use $shipyard {parent}",
            f"repo={repo}",
        ]
    )


def self_test() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        fake_bin = root / "bin"
        fake_bin.mkdir()
        gh = fake_bin / "gh"
        gh.write_text(
            "#!/bin/sh\n"
            "if [ \"$2\" = create ]; then n=$(cat \"$TMPDIR/n\" 2>/dev/null || echo 0); n=$((n+1)); echo $n > \"$TMPDIR/n\"; [ \"$FAIL_CREATE\" = \"$n\" ] && exit 1; echo https://github.com/o/r/issues/$n; exit 0; fi\n"
            "exit 0\n"
        )
        gh.chmod(0o755)
        old_path = os.environ["PATH"]
        old_tmpdir = os.environ.get("TMPDIR", "")
        os.environ["PATH"] = f"{fake_bin}:{old_path}"
        os.environ["TMPDIR"] = tmp
        try:
            plan = {
                "tracker": {"title": "Tracker", "goal": "Goal.", "constraints": ["C."], "non_goals": ["N."], "definition_of_done": ["D."]},
                "issues": [
                    {"id": "a", "title": "A", "purpose": "A.", "context": ["A."], "acceptance": ["A."], "testing": {"seam": "public API", "validation": "pytest tests/test_a.py", "do_not_test": "private helpers"}, "blocked_by": [], "blocks": ["b"], "parallelism": "First."},
                    {"id": "b", "title": "B", "role": "final_check", "purpose": "B.", "context": ["B."], "acceptance": ["B."], "testing": {"seam": "final integration", "validation": "pytest", "do_not_test": "child-owned internals"}, "blocked_by": ["a"], "blocks": [], "parallelism": "Second."},
                ],
                "waves": [{"name": "Wave 0", "items": ["a"], "notes": "Start."}, {"name": "Wave 1", "items": ["b"], "notes": "End."}],
            }
            plan_path = root / "plan.json"
            plan_path.write_text(json.dumps(plan))
            numbers = publish(plan_path, "o/r", ["enhancement"], root / "out")
            assert numbers == {"a": "#1", "b": "#2", "tracker": "#3"}
            assert "#3" in (root / "out" / "01-a.md").read_text()
            block = execution_block(plan_path, numbers, "o/r", root, root / "out" / "numbers.json")
            assert "parent_issue=#3" in block
            assert "child_issues=#1 #2" in block
            assert "final_check_issue=#2" in block
            assert f"numbers_json={(root / 'out' / 'numbers.json').resolve()}" in block
            assert f"shipyard_worktree={root}" in block
            assert "shipyard_command=Use $shipyard #3" in block
            assert json.loads((root / "out" / "publish-state.json").read_text())["repo"] == "o/r"

            try:
                publish(plan_path, "o/r", ["enhancement"], root / "out")
            except SystemExit as error:
                assert "--resume" in str(error)
            else:
                raise AssertionError("existing publish state must require --resume")
            assert publish(plan_path, "o/r", ["enhancement"], root / "out", resume=True) == numbers
            assert (root / "n").read_text().strip() == "3"
            try:
                publish(plan_path, "other/repo", ["enhancement"], root / "out", resume=True)
            except SystemExit as error:
                assert "does not match" in str(error)
            else:
                raise AssertionError("resume must reject a different repository")

            (root / "n").write_text("0")
            os.environ["FAIL_CREATE"] = "2"
            partial_out = root / "partial"
            try:
                publish(plan_path, "o/r", ["enhancement"], partial_out)
            except subprocess.CalledProcessError:
                assert json.loads((partial_out / "numbers.json").read_text()) == {"a": "#1"}
            else:
                raise AssertionError("simulated publish failure must stop")
            os.environ.pop("FAIL_CREATE")
            resumed = publish(plan_path, "o/r", ["enhancement"], partial_out, resume=True)
            assert resumed == {"a": "#1", "b": "#3", "tracker": "#4"}
        finally:
            os.environ.pop("FAIL_CREATE", None)
            os.environ["PATH"] = old_path
            if old_tmpdir:
                os.environ["TMPDIR"] = old_tmpdir
            else:
                os.environ.pop("TMPDIR", None)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("plan", nargs="?")
    parser.add_argument("--repo")
    parser.add_argument("--label", action="append", default=[])
    parser.add_argument("--out", default=".context/issues")
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--verify", action="store_true", help="Run self-tests before publishing")
    parser.add_argument("--resume", action="store_true", help="Continue from checkpointed numbers.json")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return
    if not args.plan or not args.repo:
        raise SystemExit("plan and --repo are required")
    if args.verify:
        render_self_test()
        self_test()
    plan_path = Path(args.plan)
    out = Path(args.out)
    numbers = publish(plan_path, args.repo, args.label, out, args.resume)
    print(execution_block(plan_path, numbers, args.repo, Path.cwd(), out / "numbers.json"))


if __name__ == "__main__":
    main()
