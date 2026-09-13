#!/usr/bin/env python3
"""Focused checks for GitHub CLI help compaction."""

from pathlib import Path
import sys


sys.path.insert(0, str(Path(__file__).parent))
from compact import FACETS, render_help  # noqa: E402


ROOT = Path(__file__).resolve().parents[1] / "references" / "commands"


def render(*path: str) -> dict[str, str]:
    return render_help(ROOT.joinpath(*path, "help.txt").read_text(), tuple(path))


def assert_clean(files: dict[str, str]) -> None:
    assert set(files) <= set(FACETS)
    for content in files.values():
        assert content.endswith("\n") and not content.endswith("\n\n")
        assert all(line == line.rstrip() for line in content.splitlines())


def main() -> int:
    leaf = render("pr", "create")
    assert set(leaf) == {"README.md", "examples.md", "details.md"}
    assert "# gh pr create" in leaf["README.md"]
    assert "`gh pr create [flags]`" in leaf["README.md"]
    assert "--dry-run" in leaf["README.md"]
    assert "--help" not in leaf["README.md"]
    assert "May still push git changes" in leaf["README.md"]
    assert "When the current branch isn't fully pushed" in leaf["details.md"]
    assert "gh pr create --title" in leaf["examples.md"]
    assert "LEARN MORE" not in "".join(leaf.values())
    assert_clean(leaf)

    parent = render("pr")
    assert "[`create`](create/) — Create a pull request" in parent["README.md"]
    assert "[`checkout`](checkout/) — Check out a pull request" in parent["README.md"]
    assert "A pull request can be supplied" in parent["details.md"]
    assert_clean(parent)

    cobra = render("stack")
    assert "[`submit`](submit/) — Create a stack of PRs" in cobra["README.md"]
    assert "--version" in cobra["README.md"]
    assert "https://gh.io/stacks-feedback" in cobra["details.md"]
    assert 'Use "gh stack [command] --help"' not in cobra["README.md"]
    assert "--help" not in cobra["README.md"]
    assert_clean(cobra)

    help_only = render("gpg-key", "list")
    assert set(help_only) == {"README.md"}
    assert_clean(help_only)

    print("gh compact tests ok: built-in leaf, parent, Cobra parent, universal help")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
