#!/usr/bin/env python3
"""Load exact, token-bounded Obsidian memory context for project topics."""

from __future__ import annotations

import argparse
import os
import re
import tempfile
from pathlib import Path

from obsidian_project import resolve_memory_index, topic_slug, unsymlinked_path

DEFAULT_OUT = ".context/memory-context.md"
MAX_NOTES = 2
MAX_CONTEXT_CHARS = 6000


def resolve_router(project_root: Path) -> Path:
    return resolve_memory_index(project_root)


def memory_root_for(router: Path) -> Path:
    for parent in [router.parent, *router.parents]:
        if parent.name == "projects":
            return parent.parent
    return Path(os.environ.get("OBSIDIAN_ROOT", router.parent)).expanduser().resolve()


def resolve_wikilink(router: Path, target: str) -> Path:
    target = target.split("#", 1)[0].strip()
    if not target:
        return router
    if not target.endswith(".md"):
        target = target + ".md"
    path = Path(target)
    if path.is_absolute():
        return path
    if target.startswith("projects/"):
        return memory_root_for(router) / target
    return router.parent / target


def linked_notes(router: Path) -> list[Path]:
    text = router.read_text(encoding="utf-8", errors="ignore")
    targets = re.findall(r"\[\[([^\]|#]+)(?:#[^\]|]+)?(?:\|[^\]]+)?\]\]", text)
    targets += re.findall(r"\[[^\]]+\]\(([^)]+\.md)\)", text)
    notes: list[Path] = []
    seen: set[Path] = set()
    memory_dir = router.parent.resolve()
    approved_dirs = {
        unsymlinked_path(memory_dir, "Decisions"),
        unsymlinked_path(memory_dir, "Guidance"),
    }
    for target in targets:
        note = resolve_wikilink(router, target)
        resolved = note.resolve()
        if not note.exists():
            continue
        if resolved.parent not in approved_dirs:
            raise SystemExit(f"memory index links non-approved note: {note}")
        if resolved in seen:
            continue
        seen.add(resolved)
        notes.append(note)
    return notes


def topic_routes(router: Path) -> dict[str, Path]:
    routes: dict[str, Path] = {}
    for note in linked_notes(router):
        topic = topic_slug(note.stem)
        previous = routes.get(topic)
        if previous and previous.resolve() != note.resolve():
            raise SystemExit(f"duplicate memory topic '{topic}': {previous}, {note}")
        routes[topic] = note
    return routes


def select_notes(router: Path, topics: list[str]) -> list[Path]:
    requested = list(dict.fromkeys(topic_slug(topic) for topic in topics))
    if not requested:
        raise SystemExit("at least one memory topic is required")
    if len(requested) > MAX_NOTES:
        raise SystemExit(f"at most {MAX_NOTES} memory topics may be loaded")
    routes = topic_routes(router)
    missing = [topic for topic in requested if topic not in routes]
    if missing:
        raise SystemExit("memory topic not found: " + ", ".join(missing))
    return [routes[topic] for topic in requested]


def load_context(router: Path, topics: list[str]) -> tuple[str, list[Path]]:
    if not router.exists():
        raise SystemExit(f"agent memory index not found: {router}")
    selected = select_notes(router, topics)
    root = memory_root_for(router)
    headings: list[str] = []
    for path in selected:
        try:
            rel = path.relative_to(root)
        except ValueError:
            rel = path.relative_to(router.parent)
        headings.append(f"\n## {rel.as_posix()}\n\n")
    prefix = "# Memory Context\n"
    body_limit = max(
        0,
        (MAX_CONTEXT_CHARS - len(prefix) - sum(map(len, headings))) // len(selected),
    )
    context = prefix
    for path, heading in zip(selected, headings, strict=True):
        body = path.read_text(encoding="utf-8", errors="ignore").strip()
        if len(body) > body_limit:
            body = body[: max(0, body_limit - 4)].rstrip() + "\n..."
        context += heading + body
    return context[:MAX_CONTEXT_CHARS], selected


def self_test() -> None:
    with tempfile.TemporaryDirectory() as raw:
        root = Path(raw)
        memory_root = root / "memory"
        project = root / "repo"
        memory = memory_root / "projects" / "Demo" / "Platform" / "Agent" / "Memory"
        project.mkdir()
        (memory / "Guidance" / "Inbox").mkdir(parents=True)
        router = memory / "index.md"
        first = memory / "Guidance" / "issue-workbench.md"
        second = memory / "Guidance" / "review-checkpoint.md"
        inbox = memory / "Guidance" / "Inbox" / "draft.md"
        router.write_text(
            "# Memory\n\n## Guidance\n\n"
            "- [[Guidance/issue-workbench|Issue Workbench]]\n"
            "- [[Guidance/review-checkpoint|Review Checkpoint]]\n"
            "",
            encoding="utf-8",
        )
        first.write_text("# Issue Workbench\n\nExact route.\n" + "x" * 7000, encoding="utf-8")
        second.write_text("# Review Checkpoint\n\nSecond exact route.\n", encoding="utf-8")
        inbox.write_text("# Draft\n", encoding="utf-8")
        os.environ["OBSIDIAN_ROOT"] = os.fspath(memory_root)
        (project / "AGENTS.md").write_text(
            "OBSIDIAN_PROJECT=${OBSIDIAN_ROOT}/projects/Demo/Platform\n",
            encoding="utf-8",
        )

        assert resolve_router(project) == router.resolve()
        context, selected = load_context(router, ["issue workbench", "review checkpoint"])
        assert selected == [first, second]
        assert "Exact route" in context
        assert "Second exact route" in context
        assert len(context) <= MAX_CONTEXT_CHARS
        assert "\n...\n##" in context
        try:
            load_context(router, ["missing"])
        except SystemExit as exc:
            assert "memory topic not found" in str(exc)
        else:
            raise AssertionError("accepted missing memory topic")
        try:
            load_context(router, ["one", "two", "three"])
        except SystemExit as exc:
            assert "at most 2" in str(exc)
        else:
            raise AssertionError("accepted more than two memory topics")

        duplicate = memory / "Decisions" / "issue-workbench.md"
        duplicate.parent.mkdir()
        duplicate.write_text("# Duplicate\n", encoding="utf-8")
        router.write_text(
            router.read_text(encoding="utf-8") + "- [[Decisions/issue-workbench]]\n",
            encoding="utf-8",
        )
        try:
            topic_routes(router)
        except SystemExit as exc:
            assert "duplicate memory topic" in str(exc)
        else:
            raise AssertionError("accepted duplicate memory topic")

        router.write_text("# Memory\n\n- [[Guidance/Inbox/draft]]\n", encoding="utf-8")
        try:
            topic_routes(router)
        except SystemExit as exc:
            assert "non-approved note" in str(exc)
        else:
            raise AssertionError("accepted staged memory note")

        outside = root / "outside.md"
        outside.write_text("# Outside\n", encoding="utf-8")
        router.write_text(f"# Memory\n\n- [[{outside}]]\n", encoding="utf-8")
        try:
            topic_routes(router)
        except SystemExit as exc:
            assert "non-approved note" in str(exc)
        else:
            raise AssertionError("accepted memory note outside approved folders")

        escape_memory = root / "escape-memory"
        outside_dir = root / "outside-guidance"
        escape_memory.mkdir()
        outside_dir.mkdir()
        (outside_dir / "escape.md").write_text("# Escape\n", encoding="utf-8")
        (escape_memory / "Guidance").symlink_to(outside_dir, target_is_directory=True)
        escape_router = escape_memory / "index.md"
        escape_router.write_text("# Memory\n\n- [[Guidance/escape]]\n", encoding="utf-8")
        try:
            topic_routes(escape_router)
        except SystemExit as exc:
            assert "must not contain symlinks" in str(exc)
        else:
            raise AssertionError("accepted symlinked approved memory folder")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", default=".")
    parser.add_argument("--topic", action="append", default=[])
    parser.add_argument("--out", default=DEFAULT_OUT)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return
    if not args.topic:
        parser.error("--topic is required")
    project_root = Path(args.project_root).resolve()
    context, selected = load_context(resolve_router(project_root), args.topic)
    out = project_root / args.out
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(context, encoding="utf-8")
    print("memory_context_loaded=" + ",".join(topic_slug(path.stem) for path in selected))
    print(f"memory_context_out={args.out}")


if __name__ == "__main__":
    main()
