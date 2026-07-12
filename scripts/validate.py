#!/usr/bin/env python3
"""Validate the documented skills, then run each skill's declared checks."""

from __future__ import annotations

from pathlib import Path
import re
import subprocess
import sys
import tempfile


ROOT = Path(__file__).resolve().parents[1]
SECTIONS = ("🚀 Workflow skills", "🧰 Supporting skills")
INSTALL_COMMAND = "npx skills add HenryQW/skills"
SKILL_HEADING = re.compile(r"#### \[`([^`]+)`\]\(([^)]+)\)")

# Every discovered skill must be present, even when it has no local self-test.
CHECKS_BY_SKILL: dict[str, tuple[tuple[str, tuple[str, ...]], ...]] = {
    "agent-aeo": (),
    "agent-memory": (
        ("setup", ("python3", "agent-memory/scripts/setup_agent_memory.py", "--self-test")),
        ("context", ("python3", "agent-memory/scripts/memory_context.py", "--self-test")),
        ("decision append", ("python3", "agent-memory/scripts/append_decision.py", "--self-test")),
        ("distill", ("python3", "agent-memory/scripts/distill_memory.py", "--self-test")),
    ),
    "ci-repairbay": (
        ("inspect checks help", ("python3", "ci-repairbay/scripts/inspect_pr_checks.py", "--help")),
    ),
    "identify-optimizations": (),
    "issue-blueprint": (
        ("render", ("python3", "issue-blueprint/scripts/render_issue_plan.py", "--self-test")),
        ("publish", ("python3", "issue-blueprint/scripts/publish_issue_plan.py", "--self-test")),
    ),
    "issue-workbench": (
        ("issue snapshot", ("python3", "issue-workbench/scripts/issue_snapshot.py", "--self-test")),
        ("branch name", ("python3", "issue-workbench/scripts/branch_name.py", "123", "Add Thing!!")),
        ("branch start", ("python3", "issue-workbench/scripts/start_issue_branch.py", "--self-test")),
        ("integration child", ("python3", "issue-workbench/scripts/integration_child.py", "--self-test")),
        ("diff guard", ("python3", "issue-workbench/scripts/diff_guard.py")),
    ),
    "pr-launchpad": (),
    "repo-surveyor": (),
    "review-checkpoint": (),
    "review-repairbay": (
        ("fetch comments", ("python3", "review-repairbay/scripts/fetch_comments.py", "--self-test")),
    ),
    "shipyard": (
        ("manifest", ("python3", "shipyard/scripts/manifest.py", "--self-test")),
        ("parent inspection", ("python3", "shipyard/scripts/inspect_parent_issue.py", "--self-test")),
    ),
    "skill-optimizer": (),
}


class InventoryError(ValueError):
    """The repository inventory contract is invalid."""


def discover_skills(root: Path) -> dict[str, Path]:
    skills = {path.parent.name: path.parent for path in root.glob("*/SKILL.md")}
    if not skills:
        raise InventoryError("no skills discovered")
    for name, skill_dir in skills.items():
        metadata = [path for path in skill_dir.rglob("openai.yaml") if path.parent.name == "agents"]
        if len(metadata) != 1:
            raise InventoryError(f"{name}: expected 1 agents/openai.yaml, found {len(metadata)}")
    return skills


def read_inventory(readme: Path) -> list[str]:
    lines = readme.read_text().splitlines()
    if lines.count(INSTALL_COMMAND) != 1:
        raise InventoryError("expected one canonical all-skills install command")

    documented: list[str] = []
    for title in SECTIONS:
        heading = f"### {title}"
        indexes = [index for index, line in enumerate(lines) if line == heading]
        if len(indexes) != 1:
            raise InventoryError(f"expected one {heading} section, found {len(indexes)}")
        section = lines[indexes[0] + 1 :]
        next_heading = next((i for i, line in enumerate(section) if line.startswith("### ")), len(section))
        section = section[:next_heading]

        names: list[str] = []
        for index, line in enumerate(section):
            match = SKILL_HEADING.fullmatch(line)
            if not match:
                continue
            name, target = match.groups()
            if target != f"{name}/":
                raise InventoryError(f"{name}: skill heading must link to {name}/")
            next_content = next((item for item in section[index + 1 :] if item.strip()), "")
            if not next_content or next_content.startswith("#"):
                raise InventoryError(f"{name}: missing introduction")
            names.append(name)
        if names != sorted(names, key=str.casefold):
            raise InventoryError(f"{title}: skills are not sorted A-Z by name")
        documented.extend(names)
    return documented


def validate_inventory(root: Path, registry: dict[str, object]) -> list[str]:
    skills = discover_skills(root)
    rows = read_inventory(root / "README.md")
    duplicates = sorted({name for name in rows if rows.count(name) > 1})
    if duplicates:
        raise InventoryError(f"duplicate README skills: {', '.join(duplicates)}")
    discovered = set(skills)
    documented = set(rows)
    if discovered != documented:
        missing = sorted(discovered - documented)
        stale = sorted(documented - discovered)
        raise InventoryError(f"README inventory mismatch; missing={missing}, stale={stale}")
    declared = set(registry)
    if discovered != declared:
        undeclared = sorted(discovered - declared)
        stale = sorted(declared - discovered)
        raise InventoryError(f"self-test registry mismatch; undeclared={undeclared}, stale={stale}")
    return sorted(discovered)


def fixture_readme(workflow: list[str], supporting: list[str]) -> str:
    def section(title: str, names: list[str]) -> str:
        entries = [f"#### [`{name}`]({name}/)\n\nFixture introduction." for name in names]
        return "\n\n".join((f"### {title}", *entries))

    return (
        f"# Fixture\n\n## 📦 Installation\n\n```bash\n{INSTALL_COMMAND}\n```\n\n"
        f"## 🤖 What each skill automates\n\n{section(SECTIONS[0], workflow)}\n\n"
        f"{section(SECTIONS[1], supporting)}\n"
    )


def make_fixture(root: Path) -> dict[str, object]:
    for name in ("alpha", "beta", "gamma"):
        (root / name / "agents").mkdir(parents=True)
        (root / name / "SKILL.md").write_text(f"# {name}\n")
        (root / name / "agents" / "openai.yaml").write_text("interface: {}\n")
    (root / "README.md").write_text(fixture_readme(["alpha", "beta"], ["gamma"]))
    return {"alpha": (), "beta": (), "gamma": ()}


def self_test() -> None:
    cases = {
        "missing skill introduction": lambda root, registry: (root / "README.md").write_text(
            fixture_readme(["alpha", "beta"], [])
        ),
        "empty skill introduction": lambda root, registry: (root / "README.md").write_text(
            (root / "README.md").read_text().replace("\n\nFixture introduction.", "", 1)
        ),
        "bad install command": lambda root, registry: (root / "README.md").write_text(
            (root / "README.md").read_text().replace("--agent codex", "--agent wrong", 1)
        ),
        "duplicate metadata": lambda root, registry: (
            (root / "alpha" / "duplicate" / "agents").mkdir(parents=True),
            (root / "alpha" / "duplicate" / "agents" / "openai.yaml").write_text("interface: {}\n"),
        ),
        "sort drift": lambda root, registry: (root / "README.md").write_text(
            fixture_readme(["beta", "alpha"], ["gamma"])
        ),
        "undeclared skill": lambda root, registry: registry.pop("gamma"),
    }
    for name, mutate in cases.items():
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            registry = make_fixture(root)
            validate_inventory(root, registry)
            mutate(root, registry)
            try:
                validate_inventory(root, registry)
            except InventoryError:
                continue
            raise AssertionError(f"self-test did not reject {name}")
    print(f"validate self-test ok: {len(cases)} fixtures")


def main(argv: list[str]) -> int:
    if argv == ["--self-test"]:
        self_test()
        return 0
    if argv:
        print("usage: validate.py [--self-test]", file=sys.stderr)
        return 2
    try:
        skills = validate_inventory(ROOT, CHECKS_BY_SKILL)
    except (InventoryError, OSError) as error:
        print(f"inventory validation failed: {error}", file=sys.stderr)
        return 1

    count = 0
    for skill in skills:
        for name, command in CHECKS_BY_SKILL[skill]:
            count += 1
            result = subprocess.run(command, cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            if result.returncode != 0:
                print(f"{skill}: {name} failed:", file=sys.stderr)
                print(result.stdout, file=sys.stderr)
                return result.returncode
    print(f"validate ok: {count} declared checks across {len(skills)} skills")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
