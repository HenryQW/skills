#!/usr/bin/env python3
"""
Regression tests for GH Autopilot engine parsing and cycle classification.
"""

from __future__ import annotations

import io
import json
import unittest
from contextlib import redirect_stdout
from datetime import UTC, datetime
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any

import run_autopilot_loop as autopilot


class ParseSummaryTests(unittest.TestCase):
    def test_parse_summary_with_comments(self) -> None:
        body = (
            "Copilot reviewed 14 out of 14 changed files in this pull request "
            "and generated 3 comments."
        )
        parsed = autopilot.parse_summary(body)
        self.assertEqual(parsed["files_reviewed"], 14)
        self.assertEqual(parsed["files_total"], 14)
        self.assertEqual(parsed["generated_comments"], 3)
        self.assertFalse(parsed["signals_no_comments"])

    def test_parse_summary_no_comments(self) -> None:
        body = (
            "Copilot reviewed 6 out of 6 changed files in this pull request "
            "and generated no comments."
        )
        parsed = autopilot.parse_summary(body)
        self.assertEqual(parsed["files_reviewed"], 6)
        self.assertEqual(parsed["files_total"], 6)
        self.assertIsNone(parsed["generated_comments"])
        self.assertTrue(parsed["signals_no_comments"])

    def test_parse_summary_no_new_comments(self) -> None:
        body = (
            "Copilot reviewed 14 out of 14 changed files in this pull request "
            "and generated no new comments."
        )
        parsed = autopilot.parse_summary(body)
        self.assertEqual(parsed["files_reviewed"], 14)
        self.assertEqual(parsed["files_total"], 14)
        self.assertIsNone(parsed["generated_comments"])
        self.assertTrue(parsed["signals_no_comments"])


class CycleStatusTests(unittest.TestCase):
    def test_cycle_status_no_comments_terminal(self) -> None:
        review = {
            "body": (
                "Copilot reviewed 6 out of 6 changed files in this pull request "
                "and generated no comments."
            )
        }
        status, summary = autopilot.detect_cycle_status(review, normalized_threads=[])
        self.assertEqual(status, autopilot.STATUS_COMPLETED_NO_COMMENTS)
        self.assertTrue(summary["signals_no_comments"])

    def test_cycle_status_no_new_comments_terminal(self) -> None:
        review = {
            "body": (
                "Copilot reviewed 14 out of 14 changed files in this pull request "
                "and generated no new comments."
            )
        }
        status, summary = autopilot.detect_cycle_status(review, normalized_threads=[])
        self.assertEqual(status, autopilot.STATUS_COMPLETED_NO_COMMENTS)
        self.assertTrue(summary["signals_no_comments"])

    def test_cycle_status_awaiting_address_by_comment_count(self) -> None:
        review = {
            "body": (
                "Copilot reviewed 14 out of 14 changed files in this pull request "
                "and generated 3 comments."
            )
        }
        status, _ = autopilot.detect_cycle_status(review, normalized_threads=[])
        self.assertEqual(status, autopilot.STATUS_AWAITING_ADDRESS)

    def test_cycle_status_no_threads_terminal_without_signals(self) -> None:
        review = {"body": "Copilot review complete."}
        status, _ = autopilot.detect_cycle_status(review, normalized_threads=[])
        self.assertEqual(status, autopilot.STATUS_COMPLETED_NO_COMMENTS)


class NormalizeThreadsTests(unittest.TestCase):
    def test_normalize_threads_respects_cutoff(self) -> None:
        cutoff = datetime(2026, 3, 3, 0, 0, tzinfo=UTC)
        threads = [
            {
                "id": "THREAD_OLD",
                "isResolved": False,
                "isOutdated": False,
                "path": "a.py",
                "line": 10,
                "startLine": None,
                "originalLine": 10,
                "originalStartLine": None,
                "diffSide": "RIGHT",
                "startDiffSide": None,
                "comments": {
                    "nodes": [
                        {
                            "id": "COMMENT_OLD",
                            "body": "old",
                            "createdAt": "2026-03-02T23:59:00Z",
                            "updatedAt": "2026-03-02T23:59:00Z",
                            "url": "https://example.test/old",
                            "author": {"login": "copilot-pull-request-reviewer"},
                        }
                    ]
                },
            },
            {
                "id": "THREAD_NEW",
                "isResolved": False,
                "isOutdated": False,
                "path": "b.py",
                "line": 20,
                "startLine": None,
                "originalLine": 20,
                "originalStartLine": None,
                "diffSide": "RIGHT",
                "startDiffSide": None,
                "comments": {
                    "nodes": [
                        {
                            "id": "COMMENT_NEW",
                            "body": "new",
                            "createdAt": "2026-03-03T00:01:00Z",
                            "updatedAt": "2026-03-03T00:01:00Z",
                            "url": "https://example.test/new",
                            "author": {"login": "copilot-pull-request-reviewer"},
                        }
                    ]
                },
            },
        ]

        normalized = autopilot.normalize_threads(threads, cycle_cutoff=cutoff)
        self.assertEqual(len(normalized), 1)
        self.assertEqual(normalized[0]["thread_id"], "THREAD_NEW")


class CycleArtifactTests(unittest.TestCase):
    def test_write_cycle_artifact_accepts_normalized_review_shape(self) -> None:
        with TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            pr = autopilot.GhPrRef(
                number=21,
                url="https://example.test/pr/21",
                owner="octo",
                repo="demo",
                title="PR 21",
            )
            review = {
                "id": "REVIEW_1",
                "state": "COMMENTED",
                "submitted_at": "2026-03-03T00:01:00Z",
                "author": "copilot-pull-request-reviewer",
                "body": "Copilot reviewed 1 out of 1 changed files and generated 1 comment.",
            }
            summary = autopilot.parse_summary(review["body"])

            artifacts = autopilot.write_cycle_artifact(
                output_dir,
                cycle=0,
                pr=pr,
                review=review,
                status=autopilot.STATUS_AWAITING_ADDRESS,
                summary=summary,
                threads=[],
            )

            payload = json.loads(
                Path(artifacts["cycle_json"]).read_text(encoding="utf-8")
            )
            self.assertEqual(
                payload["copilot_review"]["submitted_at"],
                "2026-03-03T00:01:00Z",
            )
            self.assertEqual(
                payload["copilot_review"]["author"],
                "copilot-pull-request-reviewer",
            )

    def test_write_cycle_artifact_accepts_graphql_review_shape(self) -> None:
        with TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            pr = autopilot.GhPrRef(
                number=22,
                url="https://example.test/pr/22",
                owner="octo",
                repo="demo",
                title="PR 22",
            )
            review = {
                "id": "REVIEW_2",
                "state": "COMMENTED",
                "submittedAt": "2026-03-03T00:02:00Z",
                "author": {"login": "copilot-pull-request-reviewer"},
                "body": "Copilot reviewed 2 out of 2 changed files and generated 1 comment.",
            }
            summary = autopilot.parse_summary(review["body"])

            artifacts = autopilot.write_cycle_artifact(
                output_dir,
                cycle=0,
                pr=pr,
                review=review,
                status=autopilot.STATUS_AWAITING_ADDRESS,
                summary=summary,
                threads=[],
            )

            payload = json.loads(
                Path(artifacts["cycle_json"]).read_text(encoding="utf-8")
            )
            self.assertEqual(
                payload["copilot_review"]["submitted_at"],
                "2026-03-03T00:02:00Z",
            )
            self.assertEqual(
                payload["copilot_review"]["author"],
                "copilot-pull-request-reviewer",
            )


class ContextDocsTests(unittest.TestCase):
    def test_update_context_documents_creates_single_context_file(self) -> None:
        with TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            pr = autopilot.GhPrRef(
                number=42,
                url="https://example.test/pr/42",
                owner="octo",
                repo="demo",
                title="Demo PR",
            )
            state = {
                "status": autopilot.STATUS_AWAITING_ADDRESS,
                "cycle": 2,
                "timing": {
                    "initial_sleep_seconds": 300,
                    "poll_interval_seconds": 45,
                    "max_wait_seconds": 2400,
                },
                "pending_review_id": "REVIEW_PENDING",
                "last_processed_review_id": "REVIEW_PREV",
            }

            docs = autopilot.update_context_documents(
                output_dir,
                state=state,
                pr=pr,
                phase=autopilot.STATUS_AWAITING_ADDRESS,
                artifacts={
                    "cycle_json": str(output_dir / "cycle.json"),
                },
            )

            self.assertTrue(Path(docs["context"]).exists())

            context_text = Path(docs["context"]).read_text(encoding="utf-8")
            self.assertIn("## Next Actions", context_text)
            self.assertIn("Reply on Copilot thread", context_text)
            self.assertIn("finalize-cycle", context_text)
            self.assertIn("## Artifacts", context_text)
            self.assertIn("cycle_json", context_text)
            self.assertIn("## Suggested Commands", context_text)
            self.assertIn("awaiting_address", context_text)

    def test_context_file_path_is_stable_across_updates(self) -> None:
        with TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            pr = autopilot.GhPrRef(
                number=7,
                url="https://example.test/pr/7",
                owner="octo",
                repo="demo",
                title="PR 7",
            )
            init_state = {
                "status": autopilot.STATUS_INITIALIZED,
                "cycle": 0,
                "timing": {
                    "initial_sleep_seconds": 300,
                    "poll_interval_seconds": 45,
                    "max_wait_seconds": 2400,
                },
                "pending_review_id": None,
                "last_processed_review_id": None,
            }
            final_state = {
                "status": autopilot.STATUS_REREQUESTED,
                "cycle": 1,
                "timing": {
                    "initial_sleep_seconds": 300,
                    "poll_interval_seconds": 45,
                    "max_wait_seconds": 2400,
                },
                "pending_review_id": None,
                "last_processed_review_id": "REVIEW_1",
            }

            docs_init = autopilot.update_context_documents(
                output_dir,
                state=init_state,
                pr=pr,
                phase=autopilot.STATUS_INITIALIZED,
            )
            docs_final = autopilot.update_context_documents(
                output_dir,
                state=final_state,
                pr=pr,
                phase=autopilot.PHASE_FINALIZED,
            )

            self.assertEqual(docs_init["context"], docs_final["context"])
            context_text = Path(docs_final["context"]).read_text(encoding="utf-8")
            self.assertIn("Finalized cycle 1", context_text)
            self.assertIn("## Next Actions", context_text)


class FinalizeCoverageTests(unittest.TestCase):
    def _write_json(self, path: Path, payload: dict) -> None:
        path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    def _write_cycle(
        self,
        output_dir: Path,
        *,
        cycle: int,
        review_id: str,
        copilot_threads: list[dict],
        addressing: dict | None,
        status: str = "awaiting_address",
    ) -> None:
        self._write_json(
            output_dir / "cycle.json",
            {
                "version": 1,
                "status": status,
                "cycle": cycle,
                "pull_request": {"number": 42, "url": "https://example.test/pr/42"},
                "copilot_review": {
                    "id": review_id,
                    "state": "COMMENTED",
                    "submitted_at": "2026-03-04T10:00:00Z",
                    "author": "copilot-pull-request-reviewer",
                    "body": "test body",
                },
                "parsed_summary": {"generated_comments": None, "signals_no_comments": False},
                "counts": {},
                "copilot_threads": copilot_threads,
                "addressing": addressing,
            },
        )

    def _base_threads(self) -> list[dict]:
        return [
            {
                "thread_id": "THREAD_1",
                "eligible_for_addressing": True,
                "comments": [
                    {"id": "C1", "created_at": "2026-03-04T10:00:00Z"},
                    {"id": "C2", "created_at": "2026-03-04T10:05:00Z"},
                ],
            },
            {
                "thread_id": "THREAD_2",
                "eligible_for_addressing": True,
                "comments": [{"id": "C3", "created_at": "2026-03-04T10:10:00Z"}],
            },
            {
                "thread_id": "THREAD_3",
                "eligible_for_addressing": False,
                "comments": [{"id": "C4", "created_at": "2026-03-04T10:15:00Z"}],
            },
        ]

    def _base_addressing(self, *, cycle: int, review_id: str) -> dict:
        return {
            "status": "ready_for_finalize",
            "cycle": cycle,
            "review_id": review_id,
            "threads": {
                "addressed": 1,
                "rejected_with_rationale": 2,
                "needs_clarification": 0,
            },
            "thread_responses": [
                {
                    "thread_id": "THREAD_1",
                    "classification": "actionable",
                    "resolved": True,
                    "rationale_replied": False,
                },
                {
                    "thread_id": "THREAD_2",
                    "classification": "non-actionable",
                    "resolved": False,
                    "rationale_replied": True,
                },
                {
                    "thread_id": "THREAD_3",
                    "classification": "non-actionable",
                    "resolved": False,
                    "rationale_replied": True,
                },
            ],
            "comment_statuses": [
                {
                    "comment_id": "C1",
                    "thread_id": "THREAD_1",
                    "created_at": "2026-03-04T10:00:00Z",
                    "cycle": cycle,
                    "status": "action",
                },
                {
                    "comment_id": "C2",
                    "thread_id": "THREAD_1",
                    "created_at": "2026-03-04T10:05:00Z",
                    "cycle": cycle,
                    "status": "action",
                },
                {
                    "comment_id": "C3",
                    "thread_id": "THREAD_2",
                    "created_at": "2026-03-04T10:10:00Z",
                    "cycle": cycle,
                    "status": "no_action",
                },
                {
                    "comment_id": "C4",
                    "thread_id": "THREAD_3",
                    "created_at": "2026-03-04T10:15:00Z",
                    "cycle": cycle,
                    "status": "no_action",
                },
            ],
            "comments": {
                "addressed_or_rationalized": 4,
                "needs_clarification": 0,
            },
            "pushed_once": True,
        }

    def test_validate_finalize_artifacts_requires_complete_thread_and_comment_coverage(self) -> None:
        with TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            self._write_cycle(
                output_dir,
                cycle=4,
                review_id="REVIEW_4",
                copilot_threads=self._base_threads(),
                addressing=self._base_addressing(cycle=4, review_id="REVIEW_4"),
            )

            summary = autopilot.validate_finalize_artifacts(
                output_dir,
                state={"cycle": 4, "pending_review_id": "REVIEW_4"},
            )
            self.assertEqual(summary["total_threads"], 3)
            self.assertEqual(summary["total_comments"], 4)
            self.assertEqual(summary["eligible_threads"], 2)
            self.assertEqual(summary["eligible_comments"], 3)
            self.assertEqual(summary["action_comments"], 2)
            self.assertEqual(summary["no_action_comments"], 2)

    def test_finalize_cycle_fails_when_comment_coverage_is_incomplete(self) -> None:
        with TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            pr = autopilot.GhPrRef(
                number=77,
                url="https://example.test/pr/77",
                owner="octo",
                repo="demo",
                title="PR 77",
            )
            store = autopilot.AutopilotStateStore(
                state_file=output_dir / "state.json",
                events_file=output_dir / "events.jsonl",
            )
            store.save(
                {
                    "version": autopilot.STATE_VERSION,
                    "status": autopilot.STATUS_AWAITING_ADDRESS,
                    "cycle": 9,
                    "pr": pr.as_dict(),
                    "last_processed_review_id": "REVIEW_8",
                    "last_processed_review_submitted_at": "2026-03-03T00:00:00Z",
                    "pending_review_id": "REVIEW_9",
                    "pending_review_submitted_at": "2026-03-04T00:00:00Z",
                    "timing": {
                        "initial_sleep_seconds": 300,
                        "poll_interval_seconds": 45,
                        "max_wait_seconds": 2400,
                    },
                }
            )

            threads = [
                {
                    "thread_id": "THREAD_1",
                    "eligible_for_addressing": True,
                    "comments": [
                        {"id": "C1", "created_at": "2026-03-04T10:00:00Z"},
                        {"id": "C2", "created_at": "2026-03-04T10:05:00Z"},
                    ],
                }
            ]
            addressing = {
                "status": "ready_for_finalize",
                "cycle": 9,
                "review_id": "REVIEW_9",
                "threads": {
                    "addressed": 1,
                    "rejected_with_rationale": 0,
                    "needs_clarification": 0,
                },
                "thread_responses": [
                    {
                        "thread_id": "THREAD_1",
                        "classification": "actionable",
                        "resolved": True,
                        "rationale_replied": False,
                    }
                ],
                "comment_statuses": [
                    {
                        "comment_id": "C1",
                        "thread_id": "THREAD_1",
                        "created_at": "2026-03-04T10:00:00Z",
                        "cycle": 9,
                        "status": "action",
                    },
                    {
                        "comment_id": "C2",
                        "thread_id": "THREAD_1",
                        "created_at": "2026-03-04T10:05:00Z",
                        "cycle": 9,
                        "status": "action",
                    },
                ],
                "comments": {
                    "addressed_or_rationalized": 1,
                    "needs_clarification": 0,
                },
                "pushed_once": True,
            }
            self._write_cycle(
                output_dir,
                cycle=9,
                review_id="REVIEW_9",
                copilot_threads=threads,
                addressing=addressing,
            )

            class FakeClient:
                def __init__(self) -> None:
                    self.requested = False

                def re_request_copilot(self, pr_number: int) -> None:
                    self.requested = True

            client = FakeClient()
            with self.assertRaisesRegex(ValueError, "comment totals"):
                autopilot.finalize_cycle(
                    client,
                    store,
                    output_dir=output_dir,
                    pr=pr,
                    request_reviewer=True,
                )
            self.assertFalse(client.requested)

    def test_validate_finalize_artifacts_rejects_unresolved_actionable_thread(self) -> None:
        with TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            threads = [
                {
                    "thread_id": "THREAD_A",
                    "eligible_for_addressing": True,
                    "comments": [{"id": "C1", "created_at": "2026-03-04T10:00:00Z"}],
                }
            ]
            addressing = {
                "status": "ready_for_finalize",
                "cycle": 2,
                "review_id": "REVIEW_2",
                "threads": {
                    "addressed": 1,
                    "rejected_with_rationale": 0,
                    "needs_clarification": 0,
                },
                "thread_responses": [
                    {
                        "thread_id": "THREAD_A",
                        "classification": "actionable",
                        "resolved": False,
                        "rationale_replied": False,
                    }
                ],
                "comment_statuses": [
                    {
                        "comment_id": "C1",
                        "thread_id": "THREAD_A",
                        "created_at": "2026-03-04T10:00:00Z",
                        "cycle": 2,
                        "status": "action",
                    }
                ],
                "comments": {"addressed_or_rationalized": 1, "needs_clarification": 0},
                "pushed_once": True,
            }
            self._write_cycle(
                output_dir,
                cycle=2,
                review_id="REVIEW_2",
                copilot_threads=threads,
                addressing=addressing,
            )
            with self.assertRaisesRegex(ValueError, "must be marked resolved=true"):
                autopilot.validate_finalize_artifacts(
                    output_dir,
                    state={"cycle": 2, "pending_review_id": "REVIEW_2"},
                )

    def test_validate_finalize_artifacts_rejects_missing_non_actionable_rationale(self) -> None:
        with TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            threads = [
                {
                    "thread_id": "THREAD_NA",
                    "eligible_for_addressing": True,
                    "comments": [{"id": "C1", "created_at": "2026-03-04T10:00:00Z"}],
                }
            ]
            addressing = {
                "status": "ready_for_finalize",
                "cycle": 3,
                "review_id": "REVIEW_3",
                "threads": {
                    "addressed": 0,
                    "rejected_with_rationale": 1,
                    "needs_clarification": 0,
                },
                "thread_responses": [
                    {
                        "thread_id": "THREAD_NA",
                        "classification": "non-actionable",
                        "resolved": False,
                        "rationale_replied": False,
                    }
                ],
                "comment_statuses": [
                    {
                        "comment_id": "C1",
                        "thread_id": "THREAD_NA",
                        "created_at": "2026-03-04T10:00:00Z",
                        "cycle": 3,
                        "status": "no_action",
                    }
                ],
                "comments": {"addressed_or_rationalized": 1, "needs_clarification": 0},
                "pushed_once": True,
            }
            self._write_cycle(
                output_dir,
                cycle=3,
                review_id="REVIEW_3",
                copilot_threads=threads,
                addressing=addressing,
            )
            with self.assertRaisesRegex(ValueError, "must set rationale_replied=true"):
                autopilot.validate_finalize_artifacts(
                    output_dir,
                    state={"cycle": 3, "pending_review_id": "REVIEW_3"},
                )

    def test_validate_finalize_artifacts_requires_response_for_every_review_thread(self) -> None:
        with TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            threads = [
                {
                    "thread_id": "THREAD_1",
                    "eligible_for_addressing": True,
                    "comments": [{"id": "C1", "created_at": "2026-03-04T10:00:00Z"}],
                },
                {
                    "thread_id": "THREAD_2",
                    "eligible_for_addressing": False,
                    "comments": [{"id": "C2", "created_at": "2026-03-04T10:10:00Z"}],
                },
            ]
            addressing = {
                "status": "ready_for_finalize",
                "cycle": 10,
                "review_id": "REVIEW_10",
                "threads": {
                    "addressed": 1,
                    "rejected_with_rationale": 0,
                    "needs_clarification": 0,
                },
                "thread_responses": [
                    {
                        "thread_id": "THREAD_1",
                        "classification": "actionable",
                        "resolved": True,
                        "rationale_replied": False,
                    }
                ],
                "comment_statuses": [
                    {
                        "comment_id": "C1",
                        "thread_id": "THREAD_1",
                        "created_at": "2026-03-04T10:00:00Z",
                        "cycle": 10,
                        "status": "action",
                    },
                    {
                        "comment_id": "C2",
                        "thread_id": "THREAD_2",
                        "created_at": "2026-03-04T10:10:00Z",
                        "cycle": 10,
                        "status": "no_action",
                    },
                ],
                "comments": {"addressed_or_rationalized": 2, "needs_clarification": 0},
                "pushed_once": True,
            }
            self._write_cycle(
                output_dir,
                cycle=10,
                review_id="REVIEW_10",
                copilot_threads=threads,
                addressing=addressing,
            )
            with self.assertRaisesRegex(ValueError, "missing responses for review threads"):
                autopilot.validate_finalize_artifacts(
                    output_dir,
                    state={"cycle": 10, "pending_review_id": "REVIEW_10"},
                )

    def test_validate_finalize_artifacts_requires_comment_statuses_chronological_order(self) -> None:
        with TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            threads = [
                {
                    "thread_id": "THREAD_1",
                    "eligible_for_addressing": True,
                    "comments": [
                        {"id": "C1", "created_at": "2026-03-04T10:00:00Z"},
                        {"id": "C2", "created_at": "2026-03-04T10:10:00Z"},
                    ],
                }
            ]
            addressing = {
                "status": "ready_for_finalize",
                "cycle": 11,
                "review_id": "REVIEW_11",
                "threads": {
                    "addressed": 1,
                    "rejected_with_rationale": 0,
                    "needs_clarification": 0,
                },
                "thread_responses": [
                    {
                        "thread_id": "THREAD_1",
                        "classification": "actionable",
                        "resolved": True,
                        "rationale_replied": False,
                    }
                ],
                "comment_statuses": [
                    {
                        "comment_id": "C2",
                        "thread_id": "THREAD_1",
                        "created_at": "2026-03-04T10:10:00Z",
                        "cycle": 11,
                        "status": "action",
                    },
                    {
                        "comment_id": "C1",
                        "thread_id": "THREAD_1",
                        "created_at": "2026-03-04T10:00:00Z",
                        "cycle": 11,
                        "status": "action",
                    },
                ],
                "comments": {"addressed_or_rationalized": 2, "needs_clarification": 0},
                "pushed_once": True,
            }
            self._write_cycle(
                output_dir,
                cycle=11,
                review_id="REVIEW_11",
                copilot_threads=threads,
                addressing=addressing,
            )
            with self.assertRaisesRegex(ValueError, "sorted chronologically"):
                autopilot.validate_finalize_artifacts(
                    output_dir,
                    state={"cycle": 11, "pending_review_id": "REVIEW_11"},
                )

    def test_validate_finalize_artifacts_rejects_comment_status_cycle_mismatch(self) -> None:
        with TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            addressing = self._base_addressing(cycle=12, review_id="REVIEW_12")
            addressing["comment_statuses"][0]["cycle"] = 99
            self._write_cycle(
                output_dir,
                cycle=12,
                review_id="REVIEW_12",
                copilot_threads=self._base_threads(),
                addressing=addressing,
            )
            with self.assertRaisesRegex(ValueError, "expected `12`"):
                autopilot.validate_finalize_artifacts(
                    output_dir,
                    state={"cycle": 12, "pending_review_id": "REVIEW_12"},
                )

    def test_finalize_cycle_writes_comment_status_history(self) -> None:
        with TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            pr = autopilot.GhPrRef(
                number=88,
                url="https://example.test/pr/88",
                owner="octo",
                repo="demo",
                title="PR 88",
            )
            store = autopilot.AutopilotStateStore(
                state_file=output_dir / "state.json",
                events_file=output_dir / "events.jsonl",
            )
            store.save(
                {
                    "version": autopilot.STATE_VERSION,
                    "status": autopilot.STATUS_AWAITING_ADDRESS,
                    "cycle": 12,
                    "pr": pr.as_dict(),
                    "last_processed_review_id": "REVIEW_11",
                    "last_processed_review_submitted_at": "2026-03-04T09:00:00Z",
                    "pending_review_id": "REVIEW_12",
                    "pending_review_submitted_at": "2026-03-04T10:00:00Z",
                    "timing": {
                        "initial_sleep_seconds": 300,
                        "poll_interval_seconds": 45,
                        "max_wait_seconds": 2400,
                    },
                }
            )
            threads = [
                {
                    "thread_id": "THREAD_1",
                    "eligible_for_addressing": True,
                    "comments": [{"id": "C1", "created_at": "2026-03-04T10:00:00Z"}],
                }
            ]
            addressing = {
                "status": "ready_for_finalize",
                "cycle": 12,
                "review_id": "REVIEW_12",
                "threads": {
                    "addressed": 1,
                    "rejected_with_rationale": 0,
                    "needs_clarification": 0,
                },
                "thread_responses": [
                    {
                        "thread_id": "THREAD_1",
                        "classification": "actionable",
                        "resolved": True,
                        "rationale_replied": False,
                    }
                ],
                "comment_statuses": [
                    {
                        "comment_id": "C1",
                        "thread_id": "THREAD_1",
                        "created_at": "2026-03-04T10:00:00Z",
                        "cycle": 12,
                        "status": "action",
                    }
                ],
                "comments": {"addressed_or_rationalized": 1, "needs_clarification": 0},
                "pushed_once": True,
            }
            self._write_cycle(
                output_dir,
                cycle=12,
                review_id="REVIEW_12",
                copilot_threads=threads,
                addressing=addressing,
            )

            class FakeClient:
                pass

            exit_code = autopilot.finalize_cycle(
                FakeClient(),
                store,
                output_dir=output_dir,
                pr=pr,
                request_reviewer=False,
            )
            self.assertEqual(exit_code, 0)

            history_path = output_dir / "comment-status-history.json"
            self.assertTrue(history_path.exists())
            payload = json.loads(history_path.read_text(encoding="utf-8"))
            self.assertEqual(len(payload["comments"]), 1)
            self.assertEqual(payload["comments"][0]["comment_id"], "C1")
            self.assertEqual(payload["comments"][0]["cycle"], 12)
            self.assertEqual(payload["comments"][0]["status"], "action")

    def test_write_comment_status_history_merges_and_sorts(self) -> None:
        with TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            existing = {
                "version": 1,
                "updated_at": "2026-03-04T11:00:00Z",
                "comments": [
                    {
                        "comment_id": "C2",
                        "thread_id": "THREAD_1",
                        "review_id": "REVIEW_OLD",
                        "cycle": 5,
                        "status": "action",
                        "created_at": "2026-03-04T10:10:00Z",
                        "updated_at": "2026-03-04T11:00:00Z",
                    }
                ],
            }
            self._write_json(output_dir / "comment-status-history.json", existing)

            written = autopilot.write_comment_status_history(
                output_dir,
                review_id="REVIEW_NEW",
                comment_statuses=[
                    {
                        "comment_id": "C1",
                        "thread_id": "THREAD_1",
                        "created_at": "2026-03-04T10:00:00Z",
                        "cycle": 6,
                        "status": "no_action",
                    },
                    {
                        "comment_id": "C2",
                        "thread_id": "THREAD_1",
                        "created_at": "2026-03-04T10:10:00Z",
                        "cycle": 6,
                        "status": "action",
                    },
                ],
            )

            payload = json.loads(written.read_text(encoding="utf-8"))
            ids = [item["comment_id"] for item in payload["comments"]]
            self.assertEqual(ids, ["C1", "C2"])
            c2 = next(item for item in payload["comments"] if item["comment_id"] == "C2")
            self.assertEqual(c2["cycle"], 6)
            self.assertEqual(c2["review_id"], "REVIEW_NEW")


class Stage2LoopTests(unittest.TestCase):
    class _FakeClient:
        def ensure_auth(self) -> None:
            return None

        def resolve_pr(self, pr_ref: str | None) -> autopilot.GhPrRef:
            _ = pr_ref
            return autopilot.GhPrRef(
                number=200,
                url="https://example.test/pr/200",
                owner="octo",
                repo="demo",
                title="PR 200",
            )

    def _store(self, output_dir: Path) -> autopilot.AutopilotStateStore:
        return autopilot.AutopilotStateStore(
            state_file=output_dir / "state.json",
            events_file=output_dir / "events.jsonl",
        )

    def _write_initialized_state(
        self, store: autopilot.AutopilotStateStore, pr: autopilot.GhPrRef
    ) -> None:
        store.save(
            {
                "version": autopilot.STATE_VERSION,
                "status": autopilot.STATUS_INITIALIZED,
                "cycle": 0,
                "pr": pr.as_dict(),
                "last_processed_review_id": None,
                "last_processed_review_submitted_at": None,
                "pending_review_id": None,
                "pending_review_submitted_at": None,
                "timing": {
                    "initial_sleep_seconds": 300,
                    "poll_interval_seconds": 45,
                    "max_wait_seconds": 2400,
                },
            }
        )

    def test_run_stage2_loop_retries_after_per_cycle_timeout(self) -> None:
        with TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            store = self._store(output_dir)
            client = self._FakeClient()
            pr = client.resolve_pr(None)
            self._write_initialized_state(store, pr)
            monitor_file = output_dir / "monitor.json"

            original_run_cycle = autopilot.run_cycle
            observed_statuses: list[str] = []
            observed_initial_sleeps: list[int] = []

            def fake_run_cycle(
                _client: Any,
                _store: Any,
                *,
                pr: autopilot.GhPrRef,
                output_dir: Path,
                monitor_file: Path,
                initial_sleep_seconds: int,
                poll_interval_seconds: int,
                max_wait_seconds: int,
            ) -> int:
                _ = (
                    _client,
                    pr,
                    output_dir,
                    monitor_file,
                    initial_sleep_seconds,
                    poll_interval_seconds,
                    max_wait_seconds,
                )
                state = store.load()
                observed_statuses.append(str(state["status"]))
                observed_initial_sleeps.append(initial_sleep_seconds)
                if len(observed_statuses) == 1:
                    state["status"] = autopilot.STATUS_TIMEOUT
                    store.save(state)
                    return 3
                state["status"] = autopilot.STATUS_AWAITING_ADDRESS
                state["pending_review_id"] = "REVIEW_PENDING"
                store.save(state)
                return 10

            autopilot.run_cycle = fake_run_cycle
            try:
                exit_code = autopilot.run_stage2_loop(
                    client,
                    store,
                    pr=pr,
                    output_dir=output_dir,
                    monitor_file=monitor_file,
                    initial_sleep_seconds=300,
                    poll_interval_seconds=45,
                    max_wait_seconds=2400,
                    stage2_max_wait_seconds=7200,
                )
            finally:
                autopilot.run_cycle = original_run_cycle

            self.assertEqual(exit_code, 10)
            self.assertEqual(
                observed_statuses,
                [autopilot.STATUS_INITIALIZED, autopilot.STATUS_INITIALIZED],
            )
            self.assertEqual(observed_initial_sleeps, [0, 300])

    def test_run_stage2_loop_stops_at_stage2_time_limit(self) -> None:
        with TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            store = self._store(output_dir)
            client = self._FakeClient()
            pr = client.resolve_pr(None)
            self._write_initialized_state(store, pr)
            monitor_file = output_dir / "monitor.json"

            original_run_cycle = autopilot.run_cycle
            original_monotonic = autopilot.time.monotonic
            monotonic_values = iter([100.0, 100.0, 100.2, 101.1, 101.3, 101.6])

            def fake_monotonic() -> float:
                return next(monotonic_values)

            def fake_run_cycle(
                _client: Any,
                _store: Any,
                *,
                pr: autopilot.GhPrRef,
                output_dir: Path,
                monitor_file: Path,
                initial_sleep_seconds: int,
                poll_interval_seconds: int,
                max_wait_seconds: int,
            ) -> int:
                _ = (
                    _client,
                    pr,
                    output_dir,
                    monitor_file,
                    initial_sleep_seconds,
                    poll_interval_seconds,
                    max_wait_seconds,
                )
                state = store.load()
                state["status"] = autopilot.STATUS_TIMEOUT
                store.save(state)
                return 3

            autopilot.run_cycle = fake_run_cycle
            autopilot.time.monotonic = fake_monotonic
            try:
                exit_code = autopilot.run_stage2_loop(
                    client,
                    store,
                    pr=pr,
                    output_dir=output_dir,
                    monitor_file=monitor_file,
                    initial_sleep_seconds=300,
                    poll_interval_seconds=45,
                    max_wait_seconds=2400,
                    stage2_max_wait_seconds=1,
                )
            finally:
                autopilot.run_cycle = original_run_cycle
                autopilot.time.monotonic = original_monotonic

            self.assertEqual(exit_code, autopilot.EXIT_STAGE2_MAX_WAIT_REACHED)
            self.assertEqual(store.load()["status"], autopilot.STATUS_TIMEOUT)


class AssertDrainedTests(unittest.TestCase):
    def _store(self, output_dir: Path) -> autopilot.AutopilotStateStore:
        return autopilot.AutopilotStateStore(
            state_file=output_dir / "state.json",
            events_file=output_dir / "events.jsonl",
        )

    def _write_state(self, store: autopilot.AutopilotStateStore, status: str) -> None:
        store.save(
            {
                "version": autopilot.STATE_VERSION,
                "status": status,
                "cycle": 7,
                "pr": {
                    "number": 533,
                    "owner": "Neuralogy",
                    "repo": "orbal-backend",
                    "title": "Example PR",
                    "url": "https://example.test/pr/533",
                },
                "last_processed_review_id": "REVIEW_6",
                "last_processed_review_submitted_at": "2026-03-02T22:05:02Z",
                "pending_review_id": "REVIEW_7",
                "pending_review_submitted_at": "2026-03-02T22:11:30Z",
                "timing": {
                    "initial_sleep_seconds": 300,
                    "poll_interval_seconds": 45,
                    "max_wait_seconds": 2400,
                },
            }
        )

    def test_assert_drained_blocks_awaiting_address(self) -> None:
        with TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            store = self._store(output_dir)
            self._write_state(store, autopilot.STATUS_AWAITING_ADDRESS)

            (output_dir / "cycle.json").write_text(
                json.dumps(
                    {
                        "version": 1,
                        "status": "awaiting_address",
                        "cycle": 7,
                        "pull_request": {"number": 533, "url": "https://example.test/pr/533"},
                        "copilot_review": {"id": "REVIEW_7"},
                        "copilot_threads": [
                            {
                                "thread_id": "THREAD_1",
                                "eligible_for_addressing": True,
                                "comments": [{"id": "C1"}],
                            }
                        ],
                        "addressing": None,
                    }
                ),
                encoding="utf-8",
            )

            captured = io.StringIO()
            with redirect_stdout(captured):
                exit_code = autopilot.command_assert_drained(
                    store, output_dir=output_dir, pr_ref="533"
                )

            payload = json.loads(captured.getvalue())
            self.assertEqual(exit_code, autopilot.EXIT_BLOCKED_UNADDRESSED)
            self.assertEqual(payload["status"], autopilot.STATUS_BLOCKED_UNADDRESSED)
            self.assertEqual(payload["cycle_artifact"]["total_threads"], 1)
            self.assertEqual(payload["cycle_artifact"]["total_comments"], 1)
            self.assertEqual(payload["cycle_artifact"]["eligible_threads"], 1)
            self.assertEqual(payload["cycle_artifact"]["eligible_comments"], 1)

    def test_assert_drained_passes_when_not_awaiting(self) -> None:
        with TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            store = self._store(output_dir)
            self._write_state(store, autopilot.STATUS_COMPLETED_NO_COMMENTS)

            captured = io.StringIO()
            with redirect_stdout(captured):
                exit_code = autopilot.command_assert_drained(
                    store, output_dir=output_dir, pr_ref="533"
                )

            payload = json.loads(captured.getvalue())
            self.assertEqual(exit_code, 0)
            self.assertEqual(payload["status"], "drained")


if __name__ == "__main__":
    unittest.main()
