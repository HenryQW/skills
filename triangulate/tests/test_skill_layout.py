#!/usr/bin/env python3
"""Regression tests for triangulate skill packaging invariants."""

from __future__ import annotations

import re
import unittest
from pathlib import Path


SKILL_PATH = Path(__file__).resolve().parents[1] / "triangulate" / "SKILL.md"
RELATIVE_MARKDOWN_PATH = re.compile(r"`((?:\./|\.\./)[^`\n]+\.md)`")


class TriangulateSkillLayoutTests(unittest.TestCase):
    def test_relative_prompt_files_live_inside_skill_directory(self) -> None:
        skill_dir = SKILL_PATH.parent.resolve()
        references_dir = skill_dir / "references"
        skill_text = SKILL_PATH.read_text(encoding="utf-8")

        referenced_paths = RELATIVE_MARKDOWN_PATH.findall(skill_text)
        self.assertTrue(referenced_paths, "expected relative markdown prompt references")

        for relative_path in referenced_paths:
            resolved = (skill_dir / relative_path).resolve()
            self.assertTrue(
                relative_path.startswith("./references/"),
                f"prompt reference must use references/: {relative_path}",
            )
            self.assertTrue(
                resolved.is_relative_to(references_dir),
                (
                    "referenced prompt file must ship inside references/: "
                    f"{relative_path}"
                ),
            )
            self.assertTrue(
                resolved.is_file(),
                f"referenced prompt file is missing: {relative_path}",
            )


if __name__ == "__main__":
    unittest.main()
