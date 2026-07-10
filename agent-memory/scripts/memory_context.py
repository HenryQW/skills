#!/usr/bin/env python3
"""Load compact Obsidian-backed memory context for a project task."""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import tempfile
from pathlib import Path

INDEX_NAME = "index.md"
LEGACY_ROUTER_NAME = "Memory Router.md"
DEFAULT_OUT = ".context/memory-context.md"
STOPWORDS = {
    "the", "and", "for", "with", "from", "that", "this", "issue", "https", "github", "com", "into",
    "use", "using", "when", "where", "what", "why", "how", "are", "was", "were", "will", "shall",
}


def slug_tokens(text: str) -> set[str]:
    return {token for token in re.findall(r"[a-z0-9][a-z0-9-]{2,}", text.lower()) if token not in STOPWORDS}


def expand_memory_ref(raw: str) -> Path:
    return Path(os.path.expandvars(raw)).expanduser().resolve()


def resolve_agent_index(agent_path: Path) -> Path:
    index = agent_path / INDEX_NAME
    legacy = agent_path / "Memory" / LEGACY_ROUTER_NAME
    if index.exists() or not legacy.exists():
        return index
    return legacy


def resolve_router(project_root: Path, explicit: str | None = None, agent_path: str | None = None) -> Path:
    if explicit:
        return expand_memory_ref(explicit)
    if os.environ.get("AGENT_MEMORY_ROUTER"):
        return expand_memory_ref(os.environ["AGENT_MEMORY_ROUTER"])
    if agent_path:
        return resolve_agent_index(expand_memory_ref(agent_path))

    agents = project_root / "AGENTS.md"
    if agents.exists():
        text = agents.read_text(encoding="utf-8")
        patterns = [
            r"(`?)(\$\{AGENT_MEMORY_ROOT\}/[^`\n]*?/Agent/index\.md)\1",
            r"(`?)(\$\{AGENT_MEMORY_ROOT\}/[^`\n]*?/Agent/Memory/Memory Router\.md)\1",
        ]
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return expand_memory_ref(match.group(2))

    root = os.environ.get("AGENT_MEMORY_ROOT")
    if root:
        base = expand_memory_ref(root)
        matches = list(base.glob("projects/**/Agent/index.md")) + list(base.glob(f"projects/**/Agent/Memory/{LEGACY_ROUTER_NAME}"))
        if len(matches) == 1:
            return matches[0]
        if len(matches) > 1:
            raise SystemExit("multiple agent memory routers found; pass --memory-router or --agent-path")
    raise SystemExit("cannot resolve agent memory index; pass --memory-router/--agent-path or set AGENT_MEMORY_ROOT/AGENT_MEMORY_ROUTER")


def issue_query(project_root: Path, issue: str | None) -> str:
    if not issue:
        return ""
    number = issue.lstrip("#")
    try:
        result = subprocess.run(
            [
                "gh",
                "issue",
                "view",
                number,
                "--json",
                "title,body,labels",
                "--jq",
                '.title + "\\n" + (.body // "") + "\\n" + ([.labels[].name] | join(" "))',
            ],
            cwd=project_root,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            timeout=20,
            check=False,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return issue
    return result.stdout if result.returncode == 0 and result.stdout.strip() else issue


def memory_root_for(router: Path) -> Path:
    for parent in [router.parent, *router.parents]:
        if parent.name == "projects":
            return parent.parent
    return Path(os.environ.get("AGENT_MEMORY_ROOT", router.parent)).expanduser().resolve()


def resolve_wikilink(router: Path, target: str) -> Path:
    target = target.split("#", 1)[0].strip()
    if not target:
        return router
    if not target.endswith(".md"):
        target = target + ".md"
    raw = Path(target)
    if raw.is_absolute():
        return raw
    if target.startswith("projects/"):
        return memory_root_for(router) / target
    return router.parent / target


def linked_notes(router: Path) -> list[Path]:
    text = router.read_text(encoding="utf-8", errors="ignore")
    notes: list[Path] = []
    for match in re.findall(r"\[\[([^\]|#]+)(?:#[^\]|]+)?(?:\|[^\]]+)?\]\]", text):
        notes.append(resolve_wikilink(router, match))
    for match in re.findall(r"\[[^\]]+\]\(([^)]+\.md)\)", text):
        notes.append(resolve_wikilink(router, match))
    existing = []
    seen: set[Path] = set()
    for note in notes:
        resolved = note.resolve()
        if resolved in seen or not note.exists() or "Inbox" in note.parts:
            continue
        seen.add(resolved)
        existing.append(note)
    return existing


def candidate_notes(router: Path) -> list[Path]:
    linked = linked_notes(router)
    if linked:
        return linked
    # Legacy fallback: old Memory Router directories did not always enumerate links.
    return [
        path for path in router.parent.rglob("*.md")
        if path.resolve() != router.resolve() and "Inbox" not in path.parts
    ]


def note_header(text: str) -> str:
    lines = []
    for line in text.splitlines()[:20]:
        if line.startswith("# ") or line.startswith("**Summary**:") or line.startswith("Summary:") or line.startswith("Keywords:"):
            lines.append(line)
    return "\n".join(lines)


def score_note(path: Path, query_tokens: set[str]) -> int:
    text = path.read_text(encoding="utf-8", errors="ignore")
    header_tokens = slug_tokens(note_header(text) + " " + path.stem)
    body_tokens = slug_tokens(text[:4000])
    return 3 * len(query_tokens & header_tokens) + len(query_tokens & body_tokens)


def load_context(router: Path, query: str, max_notes: int, max_chars: int) -> tuple[str, list[Path]]:
    if not router.exists():
        raise SystemExit(f"agent memory index not found: {router}")
    project_hint = router.parent.parent.name if router.parent.name == "Agent" else router.parent.parent.parent.name
    query_tokens = slug_tokens(query + " " + project_hint)
    ranked = sorted(((score_note(path, query_tokens), path) for path in candidate_notes(router)), key=lambda item: (-item[0], str(item[1])))
    selected = [path for score, path in ranked if score > 0][:max_notes]

    parts = ["# Memory Context", "", f"Router: {router}", ""]
    if not selected:
        parts += ["No matching memory notes loaded.", ""]
        return "\n".join(parts), []

    root = memory_root_for(router)
    for path in selected:
        try:
            rel = path.relative_to(root)
        except ValueError:
            rel = path.relative_to(router.parent)
        text = path.read_text(encoding="utf-8", errors="ignore").strip()
        if len(text) > max_chars:
            text = text[:max_chars].rstrip() + "\n..."
        parts += [f"## {rel.as_posix()}", "", text, ""]
    return "\n".join(parts), selected


def self_test() -> None:
    with tempfile.TemporaryDirectory() as raw:
        root = Path(raw)
        memory_root = root / "memory"
        project = root / "repo"
        agent = memory_root / "projects" / "Demo" / "Platform" / "Agent"
        project.mkdir()
        (agent / "Guidance" / "Inbox").mkdir(parents=True)
        router = agent / INDEX_NAME
        note = agent / "Guidance" / "issue-workbench.md"
        inbox_note = agent / "Guidance" / "Inbox" / "draft.md"
        router.write_text(
            "# Platform Agent\n\n## Loading Rule\n\nLoad linked approved notes only.\n\n## Guidance\n\n"
            "- [[projects/Demo/Platform/Agent/Guidance/issue-workbench|Issue Workbench]] - Single issue lite route.\n"
            "- [[projects/Demo/Platform/Agent/Guidance/Inbox/draft|Draft]] - Must not load.\n",
            encoding="utf-8",
        )
        note.write_text(
            "# Issue Workbench\n**Summary**: Single issue lite route.\nKeywords: issue-workbench, lite, single issue\n\nUse issue-workbench directly for one actionable issue.\n",
            encoding="utf-8",
        )
        inbox_note.write_text("# Draft\n**Summary**: lite but staged.\n", encoding="utf-8")
        os.environ["AGENT_MEMORY_ROOT"] = os.fspath(memory_root)
        text, selected = load_context(router, "lite issue-workbench", 3, 2000)
        assert selected == [note]
        assert "Single issue lite route" in text
        assert "Inbox/draft" not in text


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", default=".")
    parser.add_argument("--memory-router")
    parser.add_argument("--agent-path")
    parser.add_argument("--issue")
    parser.add_argument("--query", action="append", default=[])
    parser.add_argument("--out", default=DEFAULT_OUT)
    parser.add_argument("--max-notes", type=int, default=5)
    parser.add_argument("--max-chars", type=int, default=6000)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return
    project_root = Path(args.project_root).resolve()
    router = resolve_router(project_root, args.memory_router, args.agent_path)
    branch = subprocess.run(["git", "branch", "--show-current"], cwd=project_root, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True).stdout
    query = "\n".join(args.query + [issue_query(project_root, args.issue), branch, project_root.name])
    context, selected = load_context(router, query, args.max_notes, args.max_chars)
    out = project_root / args.out
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(context, encoding="utf-8")
    if selected:
        print("memory_context_loaded=" + ",".join(str(path) for path in selected))
    else:
        print("memory_context_loaded=none")
    print(f"memory_context_out={out}")


if __name__ == "__main__":
    main()
