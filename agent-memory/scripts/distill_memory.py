#!/usr/bin/env python3
"""Preview or apply durable memory candidates to exact final note paths."""

from __future__ import annotations

import argparse
import json
import os
import re
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from obsidian_project import resolve_memory_index, topic_slug, unsymlinked_path
from trusted_write import WriteTarget, apply_write_plan, sha256_bytes

DEFAULT_SOURCE = ".context/decisions.jsonl"
DEFAULT_PREVIEW = ".context/memory-distill-preview.json"


def titleize(topic: str) -> str:
    return " ".join(part.capitalize() for part in re.split(r"[-_\s]+", topic.strip()) if part) or "Memory"


def resolve_router(project_root: Path) -> Path:
    return resolve_memory_index(project_root)


def load_records(path: Path) -> list[dict]:
    if not path.exists():
        return []
    rows: list[dict] = []
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError as exc:
            raise SystemExit(f"{path}:{number}: invalid JSON: {exc}") from exc
        row_type = row.get("type", "decision")
        if not row.get("durable", True) or row_type not in {"decision", "guidance"}:
            continue
        required = ("topic", "source") + (("decision", "reason") if row_type == "decision" else ("guidance",))
        missing = [key for key in required if not row.get(key)]
        if missing:
            raise SystemExit(f"{path}:{number}: missing {', '.join(missing)}")
        rows.append(row)
    return rows


def row_value(row: dict, kind: str) -> str:
    key = "guidance" if kind == "guidance" else "decision"
    return str(row.get(key, "")).strip()


def update_frontmatter_date(text: str, today: str) -> str:
    if not text.startswith("---\n"):
        return text
    end = text.find("\n---", 4)
    if end == -1:
        return text
    head = text[:end]
    body = text[end:]
    if "last_updated:" in head:
        head = re.sub(r"last_updated:.*", f"last_updated: '{today}'", head)
    else:
        head += f"\nlast_updated: '{today}'"
    return head + body


def render_note(existing: str | None, topic: str, rows: list[dict], kind: str, today: str) -> str | None:
    if existing is None:
        text = (
            "---\n"
            "type: project-note\n"
            f"created: '{today}'\n"
            f"last_updated: '{today}'\n"
            "tags: []\n"
            "---\n"
            f"# {titleize(topic)}\n\n"
        )
        if kind == "decision":
            text += f"## Date\n\n{today}.\n\n## Decision\n"
        else:
            text += "## Use When\n\n- Apply this guidance when working on this topic.\n\n## Guidance\n"
    else:
        text = existing
    section = "## Guidance" if kind == "guidance" else "## Decision"
    if section not in text:
        text = text.rstrip() + f"\n\n{section}\n"
    additions = []
    seen_values: set[str] = set()
    for row in rows:
        value = row_value(row, kind)
        if not value or value in text or value in seen_values:
            continue
        seen_values.add(value)
        if kind == "decision":
            files = ", ".join(row.get("files", []))
            file_suffix = f" Files: {files}." if files else ""
            additions.append(f"- **{value}** Reason: {row['reason']} Source: {row['source']}.{file_suffix}")
        else:
            additions.append(f"- {value} Source: {row['source']}.")
    if not additions:
        return None
    return update_frontmatter_date(text.rstrip() + "\n" + "\n".join(additions) + "\n", today)


def render_router(existing: str, targets: list[Path]) -> str | None:
    additions = []
    for target in targets:
        link = target.with_suffix("").as_posix()
        if re.search(rf"\[\[{re.escape(link)}(?:[|#\]])", existing):
            continue
        additions.append(f"- [[{link}|{titleize(target.stem)}]]")
    if not additions:
        return None
    return existing.rstrip() + "\n\n" + "\n".join(additions) + "\n"


def file_hash(path: Path) -> str | None:
    return sha256_bytes(path.read_bytes()) if path.exists() else None


def apply_preview(
    source: Path,
    router: Path,
    preview_path: Path,
    write_plan=apply_write_plan,
) -> tuple[str, list[Path]]:
    if not preview_path.exists():
        raise SystemExit(f"distillation preview not found: {preview_path}; run preview first")
    try:
        preview = json.loads(preview_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SystemExit(f"invalid distillation preview: {preview_path}: {exc}") from exc
    if preview.get("version") != 1:
        raise SystemExit(f"unsupported distillation preview: {preview_path}")
    if preview.get("source") != str(source.resolve()) or preview.get("router") != str(router.resolve()):
        raise SystemExit("distillation preview belongs to a different source or memory index")
    if not source.exists() or preview.get("source_sha256") != file_hash(source):
        raise SystemExit("distillation source changed after preview; preview again")
    changes = preview.get("changes")
    if not isinstance(changes, list):
        raise SystemExit(f"invalid distillation preview changes: {preview_path}")

    memory_dir = router.parent.resolve()
    approved_folders = {
        unsymlinked_path(memory_dir, "Decisions"),
        unsymlinked_path(memory_dir, "Guidance"),
    }
    validated: list[WriteTarget] = []
    for change in changes:
        if not isinstance(change, dict) or not isinstance(change.get("target"), str) or not isinstance(change.get("content"), str):
            raise SystemExit(f"invalid distillation preview change: {preview_path}")
        relative = Path(change["target"])
        if relative.is_absolute():
            raise SystemExit(f"invalid distillation preview target: {change['target']}")
        path = memory_dir.joinpath(*relative.parts)
        rendered = change["content"]
        if path != router and path.parent not in approved_folders:
            raise SystemExit(f"invalid distillation preview target: {path}")
        if sha256_bytes(rendered.encode()) != change.get("rendered_sha256"):
            raise SystemExit(f"distillation preview content hash mismatch: {path}")
        baseline = change.get("baseline_sha256")
        if baseline is not None and not isinstance(baseline, str):
            raise SystemExit(f"invalid distillation preview baseline: {path}")
        validated.append(WriteTarget(path, baseline, rendered.encode()))
    if not validated:
        raise SystemExit(f"distillation preview has no changes: {preview_path}")

    write_plan(
        roots=(memory_dir,),
        directories=(target.path.parent for target in validated),
        targets=validated,
    )
    preview_path.unlink()
    paths = [target.path for target in validated]
    relative = ",".join(path.relative_to(memory_dir).as_posix() for path in paths)
    return f"UPDATED files={relative}", paths


def distill(
    source: Path,
    router: Path,
    preview_path: Path,
    apply: bool = False,
    today: str | None = None,
    write_plan=apply_write_plan,
) -> tuple[str, list[Path]]:
    source = source.resolve()
    router = router.resolve()
    preview_path = preview_path.resolve()
    if not router.exists():
        raise SystemExit(f"agent memory index not found: {router}")
    if apply:
        return apply_preview(source, router, preview_path, write_plan)

    rows = load_records(source)
    if not rows:
        preview_path.unlink(missing_ok=True)
        return "SKIPPED reason=no durable records", []

    grouped_rows: dict[tuple[str, str], list[dict]] = {}
    for row in rows:
        kind = "guidance" if row.get("type") == "guidance" else "decision"
        grouped_rows.setdefault((kind, topic_slug(row["topic"])), []).append(row)

    changes: list[tuple[Path, str]] = []
    routes: list[Path] = []
    memory_dir = router.parent
    today = today or datetime.now(timezone.utc).date().isoformat()
    for (kind, topic), grouped in sorted(grouped_rows.items()):
        folder = "Guidance" if kind == "guidance" else "Decisions"
        target = unsymlinked_path(memory_dir, folder, f"{topic}.md")
        routes.append(target.relative_to(memory_dir))
        existing = target.read_text(encoding="utf-8") if target.exists() else None
        rendered = render_note(existing, topic, grouped, kind, today)
        if rendered is not None:
            changes.append((target, rendered))

    rendered_router = render_router(router.read_text(encoding="utf-8"), routes)
    if rendered_router is not None:
        changes.append((router, rendered_router))

    if not changes:
        preview_path.unlink(missing_ok=True)
        return "SKIPPED reason=records already present", []

    preview = {
        "version": 1,
        "source": str(source.resolve()),
        "source_sha256": file_hash(source),
        "router": str(router.resolve()),
        "changes": [
            {
                "target": path.relative_to(memory_dir).as_posix(),
                "baseline_sha256": file_hash(path),
                "rendered_sha256": sha256_bytes(rendered.encode()),
                "content": rendered,
            }
            for path, rendered in changes
        ],
    }
    preview_path.parent.mkdir(parents=True, exist_ok=True)
    preview_path.write_text(json.dumps(preview, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
    paths = [path for path, _ in changes]
    relative = ",".join(path.relative_to(memory_dir).as_posix() for path in paths)
    return f"PREVIEW files={relative} artifact={preview_path}", paths


def self_test() -> None:
    with tempfile.TemporaryDirectory() as raw:
        root = Path(raw)
        project = root / "repo"
        memory = root / "memory" / "projects" / "Demo" / "Platform" / "Agent" / "Memory"
        project.mkdir(parents=True)
        memory.mkdir(parents=True)
        source = project / DEFAULT_SOURCE
        source.parent.mkdir()
        source.write_text(
            json.dumps(
                {
                    "type": "decision",
                    "topic": "Issue Workbench",
                    "decision": "Use lite mode for one issue.",
                    "reason": "Avoid graph overhead.",
                    "source": "self-test",
                    "durable": True,
                }
            )
            + "\n",
            encoding="utf-8",
        )
        with source.open("a", encoding="utf-8") as handle:
            handle.write(
                json.dumps(
                    {
                        "type": "guidance",
                        "topic": "Review Checkpoint",
                        "guidance": "Run blocker-only review.",
                        "source": "self-test",
                        "durable": True,
                    }
                )
                + "\n"
            )
        index = memory / "index.md"
        index.write_text("# Memory\n\n## Decisions\n", encoding="utf-8")
        os.environ["OBSIDIAN_ROOT"] = os.fspath(root / "memory")
        (project / "AGENTS.md").write_text(
            "OBSIDIAN_PROJECT=${OBSIDIAN_ROOT}/projects/Demo/Platform\n",
            encoding="utf-8",
        )
        assert resolve_router(project) == index.resolve()

        target = (memory / "Decisions" / "issue-workbench.md").resolve()
        guidance = (memory / "Guidance" / "review-checkpoint.md").resolve()
        preview_path = project / DEFAULT_PREVIEW
        status, paths = distill(source, index, preview_path, today="2026-07-10")
        assert status.startswith(
            "PREVIEW files=Decisions/issue-workbench.md,Guidance/review-checkpoint.md,index.md artifact="
        )
        assert paths == [target, guidance, index.resolve()]
        assert not target.exists() and not guidance.exists()
        preview = json.loads(preview_path.read_text(encoding="utf-8"))
        rendered = preview["changes"][0]["content"]

        original_source = source.read_text(encoding="utf-8")
        source.write_text(original_source + "\n", encoding="utf-8")
        try:
            distill(source, index, preview_path, apply=True)
        except SystemExit as exc:
            assert "source changed after preview" in str(exc)
        else:
            raise AssertionError("applied preview after source drift")
        source.write_text(original_source, encoding="utf-8")

        target.parent.mkdir(parents=True)
        target.write_text("intervening edit\n", encoding="utf-8")
        try:
            distill(source, index, preview_path, apply=True)
        except SystemExit as exc:
            assert "changed after planning" in str(exc)
        else:
            raise AssertionError("applied preview over changed final memory")
        target.unlink()

        recorded_plans = []

        def recording_write_plan(**plan):
            recorded_plans.append(plan)
            return apply_write_plan(**plan)

        status, paths = distill(
            source,
            index,
            preview_path,
            apply=True,
            today="2099-01-01",
            write_plan=recording_write_plan,
        )
        assert status == "UPDATED files=Decisions/issue-workbench.md,Guidance/review-checkpoint.md,index.md"
        assert paths == [target, guidance, index.resolve()]
        assert len(recorded_plans) == 1
        assert [item.path for item in recorded_plans[0]["targets"]] == [target, guidance, index.resolve()]
        assert target.read_text(encoding="utf-8") == rendered
        assert "Run blocker-only review." in guidance.read_text(encoding="utf-8")
        assert "[[Decisions/issue-workbench|Issue Workbench]]" in index.read_text(encoding="utf-8")
        assert "[[Guidance/review-checkpoint|Review Checkpoint]]" in index.read_text(encoding="utf-8")
        assert not preview_path.exists()

        status, paths = distill(source, index, preview_path, today="2026-07-10")
        assert status == "SKIPPED reason=records already present"
        assert paths == []

        escape_memory = root / "escape-memory"
        escape_memory.mkdir()
        escape_index = escape_memory / "index.md"
        escape_index.write_text("# Memory\n", encoding="utf-8")
        escape_preview = project / ".context/escape-preview.json"
        status, _ = distill(source, escape_index, escape_preview, today="2026-07-10")
        assert status.startswith("PREVIEW")
        outside_decisions = root / "outside-decisions"
        outside_decisions.mkdir()
        (escape_memory / "Decisions").symlink_to(outside_decisions, target_is_directory=True)
        try:
            distill(source, escape_index, escape_preview, apply=True)
        except SystemExit as exc:
            assert "must not contain symlinks" in str(exc)
        else:
            raise AssertionError("applied memory through symlinked Decisions")
        assert not (outside_decisions / "issue-workbench.md").exists()
        assert escape_preview.exists()

        symlink_memory = root / "symlink-memory"
        symlink_memory.mkdir()
        symlink_index = symlink_memory / "index.md"
        symlink_index.write_text("# Memory\n", encoding="utf-8")
        symlink_preview = project / ".context/symlink-preview.json"
        status, paths = distill(source, symlink_index, symlink_preview, today="2026-07-10")
        assert status.startswith("PREVIEW")
        target = paths[0]
        target.parent.mkdir(parents=True)
        redirected = target.with_name("redirected.md")
        target.symlink_to(redirected)
        try:
            distill(source, symlink_index, symlink_preview, apply=True)
        except SystemExit as exc:
            assert "must not contain symlinks" in str(exc)
        else:
            raise AssertionError("applied memory through a symlinked target file")
        assert not redirected.exists()
        assert symlink_preview.exists()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", default=".")
    parser.add_argument("--source", default=DEFAULT_SOURCE)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return
    project_root = Path(args.project_root).resolve()
    status, _ = distill(
        project_root / args.source,
        resolve_router(project_root),
        project_root / DEFAULT_PREVIEW,
        apply=args.apply,
    )
    print(f"memory_write={status}")


if __name__ == "__main__":
    main()
