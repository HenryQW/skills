#!/usr/bin/env python3
"""Publish rendered issue plans with gh."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import tempfile
from pathlib import Path

from render_issue_plan import render
from render_issue_plan import ordered_issues


def run(cmd: list[str]) -> str:
    return subprocess.check_output(cmd, text=True).strip()


def save(path: Path, data: dict[str, str]) -> None:
    path.write_text(json.dumps(data, indent=2) + "\n")


def publish(plan_path: Path, repo: str, labels: list[str], out: Path) -> dict[str, str]:
    render(plan_path, out, None, None)
    plan = json.loads(plan_path.read_text())
    numbers: dict[str, str] = {}
    label_args = [arg for label in labels for arg in ("--label", label)]

    for row in (out / "create-order.tsv").read_text().splitlines():
        issue_id, title, body_file = row.split("\t")
        url = run(["gh", "issue", "create", "--repo", repo, "--title", title, *label_args, "--body-file", body_file])
        numbers[issue_id] = f"#{url.rsplit('/', 1)[-1]}"

    numbers_path = out / "numbers.json"
    save(numbers_path, numbers)
    render(plan_path, out, numbers_path, None)

    tracker_title = plan["tracker"]["title"]
    tracker_url = run(["gh", "issue", "create", "--repo", repo, "--title", tracker_title, *label_args, "--body-file", str(out / "00-tracker.md")])
    numbers["tracker"] = f"#{tracker_url.rsplit('/', 1)[-1]}"
    save(numbers_path, numbers)
    render(plan_path, out, numbers_path, numbers["tracker"])

    for row in (out / "create-order.tsv").read_text().splitlines():
        issue_id, _, body_file = row.split("\t")
        run(["gh", "issue", "edit", numbers[issue_id].lstrip("#"), "--repo", repo, "--body-file", body_file])
    return numbers


def execution_block(plan_path: Path, numbers: dict[str, str], repo: str, worktree: Path) -> str:
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
            "if [ \"$2\" = create ]; then n=$(cat \"$TMPDIR/n\" 2>/dev/null || echo 0); n=$((n+1)); echo $n > \"$TMPDIR/n\"; echo https://github.com/o/r/issues/$n; exit 0; fi\n"
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
                    {"id": "a", "title": "A", "purpose": "A.", "context": ["A."], "acceptance": ["A."], "blocked_by": [], "blocks": ["b"], "parallelism": "First."},
                    {"id": "b", "title": "B", "role": "final_check", "purpose": "B.", "context": ["B."], "acceptance": ["B."], "blocked_by": ["a"], "blocks": [], "parallelism": "Second."},
                ],
                "waves": [{"name": "Wave 0", "items": ["a"], "notes": "Start."}, {"name": "Wave 1", "items": ["b"], "notes": "End."}],
            }
            plan_path = root / "plan.json"
            plan_path.write_text(json.dumps(plan))
            numbers = publish(plan_path, "o/r", ["enhancement"], root / "out")
            assert numbers == {"a": "#1", "b": "#2", "tracker": "#3"}
            assert "#3" in (root / "out" / "01-a.md").read_text()
            block = execution_block(plan_path, numbers, "o/r", root)
            assert "parent_issue=#3" in block
            assert "child_issues=#1 #2" in block
            assert "final_check_issue=#2" in block
            assert f"shipyard_worktree={root}" in block
            assert "shipyard_command=Use $shipyard #3" in block
        finally:
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
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return
    if not args.plan or not args.repo:
        raise SystemExit("plan and --repo are required")
    plan_path = Path(args.plan)
    numbers = publish(plan_path, args.repo, args.label, Path(args.out))
    print(execution_block(plan_path, numbers, args.repo, Path.cwd()))


if __name__ == "__main__":
    main()
