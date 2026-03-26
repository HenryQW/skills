"""Common fixtures for codex-subagent test suite."""

from __future__ import annotations

import io
import os
from unittest.mock import MagicMock

import pytest


# ---------------------------------------------------------------------------
# Manifest helpers
# ---------------------------------------------------------------------------


def _make_task(
    *,
    tid: str = "task-1",
    task_type: str = "review",
    prompt: str = "Do something",
    cwd: str = ".",
) -> dict[str, str]:
    return {"id": tid, "type": task_type, "prompt": prompt, "cwd": cwd}


@pytest.fixture()
def make_task():
    """Factory fixture that returns a task-dict builder."""
    return _make_task


# ---------------------------------------------------------------------------
# Mock process factory
# ---------------------------------------------------------------------------


def _make_mock_process(
    returncode: int = 0,
    stdout: bytes = b"",
    stderr: bytes = b"",
    pid: int = 12345,
) -> MagicMock:
    proc = MagicMock()
    proc.pid = pid
    proc.returncode = returncode
    proc.communicate.return_value = (stdout, stderr)
    proc.stdout = io.BytesIO(stdout)
    proc.stderr = io.BytesIO(stderr)
    proc.wait.return_value = returncode
    return proc


@pytest.fixture()
def mock_process():
    """Factory fixture returning a configurable mock subprocess."""
    return _make_mock_process


# ---------------------------------------------------------------------------
# Standard patching helpers
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _patch_which(monkeypatch):
    """Ensure shutil.which always finds a fake codex binary by default."""
    monkeypatch.setattr("shutil.which", lambda name: "/usr/bin/codex")


@pytest.fixture(autouse=True)
def _patch_subprocess_run(monkeypatch):
    """Stub subprocess.run for git and codex login calls."""

    def _fake_run(cmd, **kwargs):
        result = MagicMock()
        result.returncode = 0
        cwd = kwargs.get("cwd") or os.getcwd()
        if cmd[:3] == ["git", "rev-parse", "--show-toplevel"]:
            result.stdout = f"{cwd}\n"
        elif cmd[:2] == ["git", "status"]:
            result.stdout = b""
        else:
            result.stdout = ""
        result.stderr = ""
        return result

    monkeypatch.setattr("subprocess.run", _fake_run)


@pytest.fixture(autouse=True)
def _patch_popen(monkeypatch, mock_process):
    """Stub subprocess.Popen to return a successful mock process."""
    monkeypatch.setattr("subprocess.Popen", lambda *a, **kw: mock_process())
