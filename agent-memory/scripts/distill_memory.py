#!/usr/bin/env python3
"""Conservatively distill durable memory candidates into staged Agent notes."""

from __future__ import annotations

import argparse
import json
import os
import re
import tempfile
from datetime import datetime, timezone
from pathlib import Path

INDEX_NAME = "index.md"
LEGACY_ROUTER_NAME = "Memory Router.md"
DEFAULT_SOURCE = ".context/decisions.jsonl"


def slug(text: str) -> str:
    value = re.sub(r"[^a-z0-9-]+", "-", text.lower()).strip("-")
    return value or "decisions"


def titleize(topic: str) -> str:
    return " ".join(part.capitalize() for part in re.split(r"[-_\s]+", topic.strip()) if part) or "Decisions"


def expand(raw: str) -> Path:
    return Path(os.path.expandvars(raw)).expanduser().resolve()


def resolve_agent_index(agent_path: Path) -> Path:
    index = agent_path / INDEX_NAME
    legacy = agent_path / "Memory" / LEGACY_ROUTER_NAME
    if index.exists() or not legacy.exists():
        return index
    return legacy


def resolve_router(project_root: Path, explicit: str | None = None, agent_path: str | None = None) -> Path:
    if explicit:
        return expand(explicit)
    if os.environ.get("AGENT_MEMORY_ROUTER"):
        return expand(os.environ["AGENT_MEMORY_ROUTER"])
    if agent_path:
        return resolve_agent_index(expand(agent_path))
    agents = project_root / "AGENTS.md"
    if agents.exists():
        text = agents.read_text(encoding="utf-8")
        patterns = [
            r"\$\{AGENT_MEMORY_ROOT\}/[^`\n]*?/Agent/index\.md",
            r"\$\{AGENT_MEMORY_ROOT\}/[^`\n]*?/Agent/Memory/Memory Router\.md",
        ]
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return expand(match.group(0))
    root = os.environ.get("AGENT_MEMORY_ROOT")
    if root:
        base = expand(root)
        matches = list(base.glob("projects/**/Agent/index.md")) + list(base.glob(f"projects/**/Agent/Memory/{LEGACY_ROUTER_NAME}"))
        if len(matches) == 1:
            return matches[0]
        if len(matches) > 1:
            raise SystemExit("multiple agent memory routers found; pass --memory-router or --agent-path")
    raise SystemExit("cannot resolve agent memory index; pass --memory-router/--agent-path or set AGENT_MEMORY_ROOT/AGENT_MEMORY_ROUTER")


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


def is_new_structure(router: Path) -> bool:
    return router.name == INDEX_NAME and router.parent.name == "Agent"


def existing_note_for_topic(base: Path, topic: str) -> Path | None:
    topic_slug = slug(topic)
    for path in sorted(base.rglob("*.md")):
        if path.name in {INDEX_NAME, LEGACY_ROUTER_NAME}:
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")[:3000].lower()
        if topic_slug in slug(path.stem) or topic.lower() in text:
            return path
    return None


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


def append_to_legacy_note(note: Path, topic: str, rows: list[dict]) -> bool:
    note.parent.mkdir(parents=True, exist_ok=True)
    if note.exists():
        text = note.read_text(encoding="utf-8")
    else:
        text = (
            f"# {titleize(topic)}\n\n"
            f"Summary: Durable decisions for {topic}.\n"
            f"Keywords: {topic}, agent memory, decisions\n\n"
            "## Decisions\n"
        )
    if "## Decisions" not in text:
        text = text.rstrip() + "\n\n## Decisions\n"
    changed = False
    today = datetime.now(timezone.utc).date().isoformat()
    additions = []
    for row in rows:
        decision = row["decision"].strip()
        if decision in text:
            continue
        files = ", ".join(row.get("files", []))
        file_suffix = f" Files: {files}." if files else ""
        additions.append(f"- {today} — **{decision}** Reason: {row['reason']} Source: {row['source']}.{file_suffix}")
    if additions:
        text = text.rstrip() + "\n" + "\n".join(additions) + "\n"
        changed = True
    if changed:
        note.write_text(text, encoding="utf-8")
    return changed


def append_to_staged_note(note: Path, topic: str, rows: list[dict], kind: str) -> bool:
    note.parent.mkdir(parents=True, exist_ok=True)
    today = datetime.now(timezone.utc).date().isoformat()
    if note.exists():
        text = note.read_text(encoding="utf-8")
    else:
        title = titleize(topic)
        text = (
            "---\n"
            "type: project-note\n"
            f"created: '{today}'\n"
            f"last_updated: '{today}'\n"
            "tags: []\n"
            "---\n"
            f"# {title}\n\n"
        )
        if kind == "decision":
            text += f"## Date\n\n{today}.\n\n## Decision\n"
        else:
            text += "## Use When\n\n- Review this staged guidance before promotion.\n\n## Guidance\n"
    section = "## Decision" if kind == "decision" else "## Guidance"
    if section not in text:
        text = text.rstrip() + f"\n\n{section}\n"
    additions = []
    for row in rows:
        raw_value = row.get("decision") if kind == "decision" else row.get("guidance", row.get("decision", ""))
        value = str(raw_value or "").strip()
        if not value or value in text:
            continue
        if kind == "decision":
            files = ", ".join(row.get("files", []))
            file_suffix = f" Files: {files}." if files else ""
            additions.append(f"- **{value}** Reason: {row['reason']} Source: {row['source']}.{file_suffix}")
        else:
            additions.append(f"- {value} Source: {row['source']}.")
    if not additions:
        return False
    text = update_frontmatter_date(text.rstrip() + "\n" + "\n".join(additions) + "\n", today)
    note.write_text(text, encoding="utf-8")
    return True


def ensure_legacy_router_link(router: Path, note: Path, topic: str) -> bool:
    rel = note.relative_to(router.parent).as_posix()
    text = router.read_text(encoding="utf-8")
    if rel in text or note.stem in text:
        return False
    suffix = "" if text.endswith("\n") else "\n"
    line = f"- [{titleize(topic)}]({rel}) — durable decisions for {topic}.\n"
    if "## Memory" in text:
        text = text + suffix + line
    else:
        text = text + suffix + "\n## Memory\n\n" + line
    router.write_text(text, encoding="utf-8")
    return True


def distill(project_root: Path, source: Path, router: Path, dry_run: bool = False) -> tuple[str, list[Path]]:
    rows = load_records(source)
    if not rows:
        return "SKIPPED reason=no durable records", []
    if not router.exists():
        raise SystemExit(f"agent memory index not found: {router}")

    updated: list[Path] = []
    by_key: dict[tuple[str, str], list[dict]] = {}
    for row in rows:
        kind = "guidance" if row.get("type") == "guidance" else "decision"
        by_key.setdefault((kind, row["topic"]), []).append(row)

    if is_new_structure(router):
        agent = router.parent
        for (kind, topic), grouped in sorted(by_key.items()):
            folder = "Guidance" if kind == "guidance" else "Decisions"
            production = existing_note_for_topic(agent / folder, topic)
            staged = agent / folder / "Inbox" / f"{slug(topic)}.md"
            if production and "Inbox" not in production.parts:
                target = production
                if any((row.get("decision") or row.get("guidance", "")).strip() not in target.read_text(encoding="utf-8", errors="ignore") for row in grouped):
                    target = staged
                else:
                    continue
            else:
                target = production or staged
            if dry_run:
                updated.append(target)
                continue
            if append_to_staged_note(target, topic, grouped, kind):
                updated.append(target)
    else:
        memory_dir = router.parent
        for (_kind, topic), grouped in sorted(by_key.items()):
            note = existing_note_for_topic(memory_dir, topic) or memory_dir / "Topics" / f"{slug(topic)}.md"
            if dry_run:
                updated.append(note)
                continue
            if append_to_legacy_note(note, topic, grouped):
                updated.append(note)
            if ensure_legacy_router_link(router, note, topic):
                updated.append(router)

    if not updated:
        return "SKIPPED reason=records already present", []
    return "UPDATED files=" + ",".join(str(path) for path in updated), updated


def self_test() -> None:
    with tempfile.TemporaryDirectory() as raw:
        root = Path(raw)
        project = root / "repo"
        agent = root / "memory" / "projects" / "Demo" / "Platform" / "Agent"
        project.mkdir(parents=True)
        agent.mkdir(parents=True)
        source = project / DEFAULT_SOURCE
        source.parent.mkdir()
        source.write_text(
            json.dumps({"type": "decision", "topic": "issue-workbench", "decision": "Use lite mode for one issue.", "reason": "Avoid graph overhead.", "source": "self-test", "durable": True}) + "\n",
            encoding="utf-8",
        )
        index = agent / INDEX_NAME
        index.write_text("# Platform Agent\n\n## Decisions\n", encoding="utf-8")
        status, updated = distill(project, source, index)
        assert status.startswith("UPDATED")
        assert len(updated) == 1
        staged = agent / "Decisions" / "Inbox" / "issue-workbench.md"
        assert updated == [staged]
        assert staged.exists()
        assert "Use lite mode" in staged.read_text(encoding="utf-8")
        assert "issue-workbench" not in index.read_text(encoding="utf-8")
        status_again, updated_again = distill(project, source, index)
        assert status_again == "SKIPPED reason=records already present"
        assert updated_again == []

        legacy = root / "legacy" / "projects" / "Demo" / "Agent" / "Memory"
        legacy.mkdir(parents=True)
        router = legacy / LEGACY_ROUTER_NAME
        router.write_text("# Memory Router\n\n## Memory\n", encoding="utf-8")
        status_legacy, updated_legacy = distill(project, source, router)
        assert status_legacy.startswith("UPDATED")
        assert router in updated_legacy


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", default=".")
    parser.add_argument("--source", default=DEFAULT_SOURCE)
    parser.add_argument("--memory-router")
    parser.add_argument("--agent-path")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return
    project_root = Path(args.project_root).resolve()
    source = project_root / args.source
    router = resolve_router(project_root, args.memory_router, args.agent_path)
    if args.verify:
        load_records(source)
        if not router.exists():
            raise SystemExit(f"agent memory index not found: {router}")
    status, _ = distill(project_root, source, router, args.dry_run)
    print(f"memory_write={status}")


if __name__ == "__main__":
    main()
