"""Tests for codex-subagent parallel dispatch runner (run_batch.py).

Groups:
    1. Manifest Validation
    2. Type-to-Config Mapping
    3. Exit Code Semantics
    4. Subprocess Construction
    5. Summary Generation
"""

from __future__ import annotations

import json
from typing import Any

import pytest

from scripts.run_batch import (
    DEFAULT_CONFIG,
    MAX_OUTPUT_BYTES,
    TYPE_CONFIG,
    load_manifest,
    main,
)


# ===================================================================
# Helpers
# ===================================================================


def _write_manifest(tmp_path, data: Any) -> str:
    """Serialize *data* to a temp manifest file and return its path."""
    p = tmp_path / "manifest.json"
    p.write_text(json.dumps(data), encoding="utf-8")
    return str(p)


def _run_main(
    tmp_path,
    manifest_data: Any,
    *,
    model: str | None = None,
    monkeypatch=None,
) -> tuple[int, str]:
    """Call main() with a temp manifest and capture the exit code + stdout.

    Returns (exit_code, captured_stdout).
    """
    manifest_file = _write_manifest(tmp_path, manifest_data)
    argv = [
        "run_batch.py",
        "--manifest",
        manifest_file,
        "--run-id",
        "test-run",
    ]
    if model:
        argv.extend(["--model", model])

    if monkeypatch:
        monkeypatch.setattr("sys.argv", argv)
        monkeypatch.chdir(tmp_path)
    else:
        raise RuntimeError("monkeypatch is required")

    from io import StringIO

    captured = StringIO()
    monkeypatch.setattr("sys.stdout", captured)

    with pytest.raises(SystemExit) as exc_info:
        main()

    return exc_info.value.code, captured.getvalue()


# ===================================================================
# Group 1: Manifest Validation
# ===================================================================


class TestManifestValidation:
    """Validate manifest loading and structural checks."""

    def test_valid_manifest_passes(self, tmp_path, make_task):
        manifest = {
            "tasks": [
                make_task(tid="a", task_type="review"),
                make_task(tid="b", task_type="implement"),
            ]
        }
        path = _write_manifest(tmp_path, manifest)
        tasks = load_manifest(path)
        assert len(tasks) == 2
        assert tasks[0]["id"] == "a"
        assert tasks[1]["id"] == "b"

    def test_missing_tasks_key_fails(self, tmp_path):
        path = _write_manifest(tmp_path, {"not_tasks": []})
        with pytest.raises(SystemExit) as exc_info:
            load_manifest(path)
        assert exc_info.value.code == 2

    def test_missing_required_field_fails(self, tmp_path):
        manifest = {"tasks": [{"type": "review", "prompt": "x", "cwd": "."}]}
        path = _write_manifest(tmp_path, manifest)
        with pytest.raises(SystemExit) as exc_info:
            load_manifest(path)
        assert exc_info.value.code == 2

    def test_duplicate_ids_fails(self, tmp_path, make_task):
        manifest = {
            "tasks": [
                make_task(tid="dup"),
                make_task(tid="dup"),
            ]
        }
        path = _write_manifest(tmp_path, manifest)
        with pytest.raises(SystemExit) as exc_info:
            load_manifest(path)
        assert exc_info.value.code == 2

    def test_unknown_type_defaults_to_readonly_high(self, tmp_path, make_task):
        manifest = {"tasks": [make_task(tid="x", task_type="custom-type")]}
        path = _write_manifest(tmp_path, manifest)
        tasks = load_manifest(path)
        assert len(tasks) == 1
        cfg = TYPE_CONFIG.get(tasks[0]["type"], DEFAULT_CONFIG)
        assert cfg == {"sandbox": "read-only", "effort": "high"}

    def test_parallel_write_overlap_warns(self, tmp_path, make_task, capsys):
        manifest = {
            "tasks": [
                make_task(tid="w1", task_type="implement", cwd="/shared"),
                make_task(tid="w2", task_type="implement", cwd="/shared"),
            ]
        }
        path = _write_manifest(tmp_path, manifest)
        load_manifest(path)
        captured = capsys.readouterr()
        assert "Warning" in captured.err
        assert "/shared" in captured.err


# ===================================================================
# Group 2: Type-to-Config Mapping
# ===================================================================


class TestTypeMapping:
    """Ensure task types map to the correct sandbox + effort config."""

    @pytest.mark.parametrize("task_type", ["review", "analyze", "search", "document"])
    def test_all_readonly_types_map_correctly(self, task_type):
        cfg = TYPE_CONFIG[task_type]
        assert cfg["sandbox"] == "read-only"
        assert cfg["effort"] == "high"

    @pytest.mark.parametrize(
        "task_type", ["implement", "refactor", "debug", "architect"]
    )
    def test_all_write_types_map_correctly(self, task_type):
        cfg = TYPE_CONFIG[task_type]
        assert cfg["sandbox"] == "workspace-write"
        assert cfg["effort"] == "xhigh"

    def test_unknown_type_falls_back(self):
        assert "custom-type" not in TYPE_CONFIG
        cfg = TYPE_CONFIG.get("custom-type", DEFAULT_CONFIG)
        assert cfg["sandbox"] == "read-only"
        assert cfg["effort"] == "high"


# ===================================================================
# Group 3: Exit Code Semantics
# ===================================================================


class TestExitCodes:
    """Verify runner exit codes for success, failure, and error conditions."""

    def test_all_tasks_succeed_exit_0(
        self, tmp_path, monkeypatch, make_task, mock_process
    ):
        manifest = {
            "tasks": [
                make_task(tid="ok1", task_type="review"),
                make_task(tid="ok2", task_type="analyze"),
            ]
        }

        proc = mock_process(returncode=0, stdout=b"done")
        monkeypatch.setattr(
            "subprocess.Popen", lambda *a, **kw: mock_process(returncode=0, stdout=b"ok")
        )

        exit_code, _ = _run_main(tmp_path, manifest, monkeypatch=monkeypatch)
        assert exit_code == 0

    def test_one_task_fails_exit_1(
        self, tmp_path, monkeypatch, make_task, mock_process
    ):
        manifest = {
            "tasks": [
                make_task(tid="ok", task_type="review"),
                make_task(tid="bad", task_type="analyze"),
            ]
        }

        call_count = {"n": 0}

        def _popen(*args, **kwargs):
            call_count["n"] += 1
            if call_count["n"] == 1:
                return mock_process(returncode=0, stdout=b"good")
            return mock_process(returncode=1, stderr=b"error")

        monkeypatch.setattr("subprocess.Popen", _popen)

        exit_code, _ = _run_main(tmp_path, manifest, monkeypatch=monkeypatch)
        assert exit_code == 1

    def test_bad_manifest_exit_2(self, tmp_path, monkeypatch):
        bad_json_path = tmp_path / "manifest.json"
        bad_json_path.write_text("NOT VALID JSON", encoding="utf-8")

        monkeypatch.setattr(
            "sys.argv",
            ["run_batch.py", "--manifest", str(bad_json_path), "--run-id", "r1"],
        )
        monkeypatch.chdir(tmp_path)

        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code == 2

    def test_missing_codex_exit_2(self, tmp_path, monkeypatch, make_task):
        monkeypatch.setattr("shutil.which", lambda name: None)

        manifest = {"tasks": [make_task()]}
        manifest_file = _write_manifest(tmp_path, manifest)

        monkeypatch.setattr(
            "sys.argv",
            ["run_batch.py", "--manifest", manifest_file, "--run-id", "r1"],
        )
        monkeypatch.chdir(tmp_path)

        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code == 2


# ===================================================================
# Group 4: Subprocess Construction
# ===================================================================


class TestSubprocessConstruction:
    """Verify the shape and content of Popen calls."""

    def _capture_popen_calls(
        self,
        tmp_path,
        monkeypatch,
        make_task,
        mock_process,
        *,
        model: str | None = None,
    ) -> list[tuple[tuple, dict]]:
        """Run main() and return the (args, kwargs) of every Popen call."""
        manifest = {"tasks": [make_task(tid="sub1", task_type="review")]}

        calls: list[tuple[tuple, dict]] = []

        def _recording_popen(*args, **kwargs):
            calls.append((args, kwargs))
            return mock_process(returncode=0, stdout=b"ok")

        monkeypatch.setattr("subprocess.Popen", _recording_popen)

        _run_main(tmp_path, manifest, model=model, monkeypatch=monkeypatch)
        return calls

    def test_commands_are_lists_not_strings(
        self, tmp_path, monkeypatch, make_task, mock_process
    ):
        calls = self._capture_popen_calls(
            tmp_path, monkeypatch, make_task, mock_process
        )
        assert len(calls) >= 1
        for args, kwargs in calls:
            cmd = args[0]
            assert isinstance(cmd, list), f"Expected list, got {type(cmd)}"

    def test_shell_is_never_true(
        self, tmp_path, monkeypatch, make_task, mock_process
    ):
        calls = self._capture_popen_calls(
            tmp_path, monkeypatch, make_task, mock_process
        )
        for _, kwargs in calls:
            assert kwargs.get("shell") is not True, "shell=True must never be used"

    def test_model_flag_included_when_specified(
        self, tmp_path, monkeypatch, make_task, mock_process
    ):
        calls = self._capture_popen_calls(
            tmp_path, monkeypatch, make_task, mock_process, model="o3"
        )
        assert len(calls) >= 1
        cmd = calls[0][0][0]
        assert "-m" in cmd
        idx = cmd.index("-m")
        assert cmd[idx + 1] == "o3"

    def test_model_flag_omitted_when_not_specified(
        self, tmp_path, monkeypatch, make_task, mock_process
    ):
        calls = self._capture_popen_calls(
            tmp_path, monkeypatch, make_task, mock_process, model=None
        )
        assert len(calls) >= 1
        cmd = calls[0][0][0]
        assert "-m" not in cmd


# ===================================================================
# Group 5: Summary Generation
# ===================================================================


class TestSummaryGeneration:
    """Validate the structure and content of summary.json."""

    def _get_summary(
        self,
        tmp_path,
        monkeypatch,
        make_task,
        mock_process,
        *,
        tasks: list[dict] | None = None,
        popen_factory=None,
    ) -> dict[str, Any]:
        """Run main() and return the parsed summary dict."""
        if tasks is None:
            tasks = [make_task(tid="s1", task_type="review")]
        manifest = {"tasks": tasks}

        if popen_factory:
            monkeypatch.setattr("subprocess.Popen", popen_factory)
        else:
            monkeypatch.setattr(
                "subprocess.Popen",
                lambda *a, **kw: mock_process(returncode=0, stdout=b"output"),
            )

        _, stdout = _run_main(tmp_path, manifest, monkeypatch=monkeypatch)
        return json.loads(stdout)

    def test_summary_json_structure(
        self, tmp_path, monkeypatch, make_task, mock_process
    ):
        summary = self._get_summary(tmp_path, monkeypatch, make_task, mock_process)

        assert "run_id" in summary
        assert "total_elapsed_seconds" in summary
        assert "total_tasks" in summary
        assert "succeeded" in summary
        assert "failed" in summary
        assert "tasks" in summary
        assert isinstance(summary["tasks"], list)
        assert summary["total_tasks"] == 1

    def test_truncation_flag_at_10kb(
        self, tmp_path, monkeypatch, make_task, mock_process
    ):
        large_output = b"A" * (MAX_OUTPUT_BYTES + 1024)

        monkeypatch.setattr(
            "subprocess.Popen",
            lambda *a, **kw: mock_process(returncode=0, stdout=large_output),
        )

        summary = self._get_summary(
            tmp_path,
            monkeypatch,
            make_task,
            mock_process,
            popen_factory=lambda *a, **kw: mock_process(
                returncode=0, stdout=large_output
            ),
        )

        task_result = summary["tasks"][0]
        assert task_result["truncated"] is True
        assert len(task_result["output"].encode("utf-8")) <= MAX_OUTPUT_BYTES

    def test_per_task_fields_present(
        self, tmp_path, monkeypatch, make_task, mock_process
    ):
        tasks = [
            make_task(tid="f1", task_type="review"),
            make_task(tid="f2", task_type="implement"),
        ]

        call_count = {"n": 0}

        def _factory(*a, **kw):
            call_count["n"] += 1
            return mock_process(returncode=0, stdout=b"data")

        summary = self._get_summary(
            tmp_path,
            monkeypatch,
            make_task,
            mock_process,
            tasks=tasks,
            popen_factory=_factory,
        )

        required_fields = {
            "id",
            "type",
            "status",
            "exit_code",
            "elapsed_seconds",
            "output",
            "truncated",
        }

        for task_result in summary["tasks"]:
            missing = required_fields - set(task_result.keys())
            assert not missing, f"Task {task_result.get('id')} missing fields: {missing}"
