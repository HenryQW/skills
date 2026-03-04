#!/usr/bin/env python3
"""Tests for build_review_batch.py."""

from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

import build_review_batch as builder


class BuildReviewBatchTests(unittest.TestCase):
    def test_build_review_batch_generates_normalized_threads(self) -> None:
        cycle_payload = {
            "status": "awaiting_address",
            "cycle": 3,
            "pull_request": {"number": 12, "url": "https://example.test/pr/12"},
            "copilot_review": {"id": "REVIEW_1", "state": "COMMENTED"},
            "copilot_threads": [
                {
                    "thread_number": 1,
                    "thread_id": "THREAD_1",
                    "path": "app.py",
                    "line": 10,
                    "eligible_for_addressing": True,
                    "comments": [
                        {
                            "id": "C1",
                            "created_at": "2026-03-03T00:01:00Z",
                            "body": "first",
                        },
                        {
                            "id": "C2",
                            "created_at": "2026-03-03T00:03:00Z",
                            "body": "latest",
                        },
                    ],
                },
                {
                    "thread_number": 2,
                    "thread_id": "THREAD_2",
                    "path": "README.md",
                    "line": 2,
                    "eligible_for_addressing": False,
                    "comments": [],
                },
            ],
        }

        with TemporaryDirectory() as tmp:
            cycle_path = Path(tmp) / "cycle.json"
            cycle_path.write_text("{}", encoding="utf-8")
            batch = builder.build_review_batch(cycle_payload, cycle_path=cycle_path)

        self.assertEqual(batch["version"], builder.BATCH_VERSION)
        self.assertEqual(batch["summary"]["threads_total"], 2)
        self.assertEqual(batch["summary"]["threads_eligible"], 1)
        self.assertEqual(batch["summary"]["threads_pending"], 2)
        self.assertEqual(batch["threads"][0]["classification"], "pending")
        self.assertEqual(batch["threads"][0]["latest_comment"]["id"], "C2")
        self.assertEqual(batch["threads"][1]["latest_comment"], None)

    def test_validate_cycle_payload_requires_contract_keys(self) -> None:
        with self.assertRaisesRegex(ValueError, "missing required key"):
            builder.validate_cycle_payload({"status": "awaiting_address"})


if __name__ == "__main__":
    unittest.main()
