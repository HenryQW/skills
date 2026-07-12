#!/usr/bin/env python3
"""Apply contained multi-file writes atomically per target with rollback evidence."""

from __future__ import annotations

import ast
import hashlib
import os
import tempfile
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class WriteTarget:
    path: Path
    baseline_sha256: str | None
    content: bytes


class WritePlanError(SystemExit):
    def __init__(
        self,
        cause: str,
        committed: Iterable[Path] = (),
        restored: Iterable[Path] = (),
        unresolved: Iterable[Path] = (),
    ) -> None:
        self.committed = tuple(committed)
        self.restored = tuple(restored)
        self.unresolved = tuple(unresolved)
        super().__init__(
            f"write plan failed: {cause}; committed={_paths(self.committed)}; "
            f"restored={_paths(self.restored)}; unresolved={_paths(self.unresolved)}"
        )


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _paths(paths: Iterable[Path]) -> str:
    return "[" + ",".join(str(path) for path in paths) + "]"


def _absolute(path: Path) -> Path:
    return Path(os.path.abspath(path))


def _reject_symlinks(path: Path) -> None:
    current = Path(path.anchor)
    for part in path.parts[1:]:
        current /= part
        if current.is_symlink():
            raise ValueError(f"write path must not contain symlinks: {current}")


def _validate_path(path: Path, roots: tuple[Path, ...]) -> Path:
    path = _absolute(path)
    _reject_symlinks(path)
    if not any(path == root or path.is_relative_to(root) for root in roots):
        raise ValueError(f"write path escapes allowed roots: {path}")
    return path


def _state(path: Path) -> bytes | None:
    if path.is_symlink():
        raise ValueError(f"write target must not be a symlink: {path}")
    if not path.exists():
        return None
    if not path.is_file():
        raise ValueError(f"write target must be a regular file: {path}")
    return path.read_bytes()


def _stage(path: Path, content: bytes) -> Path:
    descriptor, raw = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    staged = Path(raw)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
    except BaseException:
        staged.unlink(missing_ok=True)
        raise
    return staged


def _rollback(path: Path, baseline: bytes | None) -> None:
    if baseline is None:
        path.unlink(missing_ok=True)
        return
    staged = _stage(path, baseline)
    try:
        os.replace(staged, path)
    finally:
        staged.unlink(missing_ok=True)


def apply_write_plan(
    *,
    roots: Iterable[Path],
    directories: Iterable[Path],
    targets: Iterable[WriteTarget],
    stage: Callable[[Path, bytes], Path] = _stage,
    replace: Callable[[Path, Path], None] = os.replace,
    readback: Callable[[Path], bytes] = Path.read_bytes,
    rollback: Callable[[Path, bytes | None], None] = _rollback,
) -> tuple[Path, ...]:
    roots = tuple(_absolute(root) for root in roots)
    directories = tuple(directories)
    targets = tuple(targets)
    if not roots:
        raise WritePlanError("no allowed roots")
    try:
        for root in roots:
            _reject_symlinks(root)
        directories = tuple(_validate_path(path, roots) for path in directories)
        targets = tuple(
            WriteTarget(_validate_path(target.path, roots), target.baseline_sha256, target.content)
            for target in targets
        )
        if len({target.path for target in targets}) != len(targets):
            raise ValueError("write plan contains duplicate targets")
    except (OSError, ValueError) as exc:
        raise WritePlanError(str(exc)) from exc

    created_directories: list[Path] = []
    staged: dict[Path, Path] = {}
    baselines: dict[Path, bytes | None] = {}
    contents = {target.path: target.content for target in targets}
    committed: list[Path] = []
    attempted: Path | None = None
    try:
        for directory in sorted(set(directories), key=lambda path: len(path.parts)):
            missing = [
                parent
                for parent in reversed(directory.parents)
                if parent in roots or any(parent.is_relative_to(root) for root in roots)
            ]
            missing.append(directory)
            for path in missing:
                if not path.exists():
                    path.mkdir()
                    created_directories.append(path)
                elif not path.is_dir():
                    raise ValueError(f"write directory is not a directory: {path}")
        for target in targets:
            _reject_symlinks(target.path)
            if not target.path.parent.is_dir():
                raise ValueError(f"write target parent does not exist: {target.path.parent}")
            baselines[target.path] = _state(target.path)
            staged[target.path] = stage(target.path, target.content)
        for target in targets:
            _reject_symlinks(target.path)
            current = _state(target.path)
            current_hash = sha256_bytes(current) if current is not None else None
            if current_hash != target.baseline_sha256:
                raise ValueError(f"write target changed after planning: {target.path}")
        for target in targets:
            _reject_symlinks(target.path)
            current = _state(target.path)
            current_hash = sha256_bytes(current) if current is not None else None
            if current_hash != target.baseline_sha256:
                raise ValueError(f"write target changed before replacement: {target.path}")
            attempted = target.path
            replace(staged[target.path], target.path)
            staged.pop(target.path, None)
            committed.append(target.path)
            if readback(target.path) != target.content:
                raise OSError(f"write readback mismatch: {target.path}")
        return tuple(committed)
    except BaseException as exc:
        if attempted is not None and attempted not in committed:
            try:
                if _state(attempted) != baselines[attempted]:
                    committed.append(attempted)
                    staged.pop(attempted, None)
            except BaseException:
                committed.append(attempted)
        restored: list[Path] = []
        unresolved: list[Path] = []
        for path in reversed(committed):
            try:
                current = _state(path)
            except BaseException:
                unresolved.append(path)
                continue
            if current == baselines[path]:
                restored.append(path)
                continue
            if current != contents[path]:
                unresolved.append(path)
                continue
            try:
                rollback(path, baselines[path])
            except BaseException:
                pass
            try:
                matches = _state(path) == baselines[path]
            except BaseException:
                matches = False
            (restored if matches else unresolved).append(path)
        for path in staged.values():
            path.unlink(missing_ok=True)
        for path in reversed(created_directories):
            try:
                path.rmdir()
            except OSError:
                pass
        if isinstance(exc, WritePlanError):
            raise
        raise WritePlanError(str(exc), committed, reversed(restored), reversed(unresolved)) from exc


def _assert_callers_cross_seam() -> None:
    def root_name(node: ast.expr) -> str | None:
        while isinstance(node, ast.Attribute):
            node = node.value
        return node.id if isinstance(node, ast.Name) else None

    mutations = {"mkdir", "unlink", "write_bytes", "write_text"}
    for filename, seam_function in (
        ("setup_agent_memory.py", "apply_setup"),
        ("distill_memory.py", "apply_preview"),
    ):
        tree = ast.parse((Path(__file__).with_name(filename)).read_text(encoding="utf-8"))
        functions = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name != "self_test"]
        function = next(node for node in functions if node.name == seam_function)
        calls = [node for node in ast.walk(function) if isinstance(node, ast.Call)]
        assert any(isinstance(call.func, ast.Name) and call.func.id == "write_plan" for call in calls)
        forbidden = []
        for production_function in functions:
            for call in (node for node in ast.walk(production_function) if isinstance(node, ast.Call)):
                if not isinstance(call.func, ast.Attribute) or root_name(call.func.value) == "preview_path":
                    continue
                if call.func.attr in mutations:
                    forbidden.append(call)
                if call.func.attr in {"replace", "rename"} and root_name(call.func.value) in {
                    "os",
                    "path",
                    "target",
                }:
                    forbidden.append(call)
                if call.func.attr == "open" and call.args and isinstance(call.args[0], ast.Constant):
                    if any(flag in str(call.args[0].value) for flag in "wax+"):
                        forbidden.append(call)
        assert not forbidden, f"{filename} writes production targets outside trusted_write"


def self_test() -> None:
    _assert_callers_cross_seam()
    with tempfile.TemporaryDirectory() as raw:
        root = Path(raw).resolve()
        a = root / "a.txt"
        b = root / "b.txt"
        a.write_bytes(b"old-a")
        b.write_bytes(b"old-b")

        def targets() -> tuple[WriteTarget, ...]:
            return (
                WriteTarget(a, sha256_bytes(b"old-a"), b"new-a"),
                WriteTarget(b, sha256_bytes(b"old-b"), b"new-b"),
            )

        staged_count = 0

        def fail_second_stage(path: Path, content: bytes) -> Path:
            nonlocal staged_count
            staged_count += 1
            if staged_count == 2:
                raise OSError("injected stage failure")
            return _stage(path, content)

        try:
            apply_write_plan(roots=(root,), directories=(), targets=targets(), stage=fail_second_stage)
        except WritePlanError as exc:
            assert not exc.committed and not exc.restored and not exc.unresolved
        else:
            raise AssertionError("accepted stage failure")
        assert a.read_bytes() == b"old-a" and b.read_bytes() == b"old-b"

        staged_count = 0

        def drift_after_staging(path: Path, content: bytes) -> Path:
            nonlocal staged_count
            staged_count += 1
            staged = _stage(path, content)
            if staged_count == 2:
                b.write_bytes(b"drift")
            return staged

        try:
            apply_write_plan(roots=(root,), directories=(), targets=targets(), stage=drift_after_staging)
        except WritePlanError as exc:
            assert staged_count == 2 and not exc.committed
        else:
            raise AssertionError("accepted baseline drift")
        assert a.read_bytes() == b"old-a" and b.read_bytes() == b"drift"
        b.write_bytes(b"old-b")

        replace_count = 0

        def fail_second_replace(source: Path, target: Path) -> None:
            nonlocal replace_count
            replace_count += 1
            if replace_count == 2:
                raise OSError("injected replace failure")
            os.replace(source, target)

        try:
            apply_write_plan(roots=(root,), directories=(), targets=targets(), replace=fail_second_replace)
        except WritePlanError as exc:
            assert exc.committed == (a,) and exc.restored == (a,) and not exc.unresolved
        else:
            raise AssertionError("accepted replace failure")
        assert a.read_bytes() == b"old-a" and b.read_bytes() == b"old-b"

        def drift_later_target(path: Path) -> bytes:
            if path == a:
                b.write_bytes(b"concurrent-b")
            return path.read_bytes()

        try:
            apply_write_plan(roots=(root,), directories=(), targets=targets(), readback=drift_later_target)
        except WritePlanError as exc:
            assert exc.committed == (a,) and exc.restored == (a,) and not exc.unresolved
        else:
            raise AssertionError("overwrote a target changed during commit")
        assert a.read_bytes() == b"old-a" and b.read_bytes() == b"concurrent-b"
        b.write_bytes(b"old-b")

        def fail_readback(path: Path) -> bytes:
            raise OSError(f"injected readback failure: {path}")

        try:
            apply_write_plan(roots=(root,), directories=(), targets=targets(), readback=fail_readback)
        except WritePlanError as exc:
            assert exc.committed == (a,) and exc.restored == (a,) and not exc.unresolved
        else:
            raise AssertionError("accepted readback failure")
        assert a.read_bytes() == b"old-a" and b.read_bytes() == b"old-b"

        def concurrent_readback(path: Path) -> bytes:
            path.write_bytes(b"concurrent-a")
            return b"mismatch"

        try:
            apply_write_plan(roots=(root,), directories=(), targets=targets(), readback=concurrent_readback)
        except WritePlanError as exc:
            assert exc.committed == (a,) and not exc.restored and exc.unresolved == (a,)
        else:
            raise AssertionError("overwrote a target changed before rollback")
        assert a.read_bytes() == b"concurrent-a" and b.read_bytes() == b"old-b"
        a.write_bytes(b"old-a")

        replace_count = 0

        def fail_rollback(path: Path, baseline: bytes | None) -> None:
            raise OSError(f"injected rollback failure: {path}")

        try:
            apply_write_plan(
                roots=(root,),
                directories=(),
                targets=targets(),
                replace=fail_second_replace,
                rollback=fail_rollback,
            )
        except WritePlanError as exc:
            assert exc.committed == (a,) and not exc.restored and exc.unresolved == (a,)
        else:
            raise AssertionError("accepted rollback failure")
        assert a.read_bytes() == b"new-a" and b.read_bytes() == b"old-b"
        a.write_bytes(b"old-a")

        outside = root.parent / "outside.txt"
        try:
            apply_write_plan(
                roots=(root,),
                directories=(),
                targets=(WriteTarget(outside, None, b"escape"),),
            )
        except WritePlanError as exc:
            assert "escapes allowed roots" in str(exc)
        else:
            raise AssertionError("accepted escaping target")

        redirected = root / "redirected"
        redirected.mkdir()
        link = root / "link"
        link.symlink_to(redirected, target_is_directory=True)
        try:
            apply_write_plan(
                roots=(root,),
                directories=(link,),
                targets=(WriteTarget(link / "target.txt", None, b"redirected"),),
            )
        except WritePlanError as exc:
            assert "symlinks" in str(exc)
        else:
            raise AssertionError("accepted symlinked target")
        assert not (redirected / "target.txt").exists()

        apply_write_plan(roots=(root,), directories=(), targets=targets())
        assert a.read_bytes() == b"new-a" and b.read_bytes() == b"new-b"
    print("trusted-write self-test ok")


if __name__ == "__main__":
    self_test()
