#!/usr/bin/env python3
"""Run PR feedback helper regression checks."""

import json
import os
from pathlib import Path
import subprocess
import tempfile


ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "pr-comment-sweep" / "scripts"
FETCHER = SCRIPTS / "fetch-pr-feedback.py"
HELPER = SCRIPTS / "pr-feedback.mjs"
VERIFIER = SCRIPTS / "verify-pr-target.sh"


def wrapper_args(wrapper: Path, *args: str) -> list[str]:
    with tempfile.TemporaryDirectory() as directory:
        worktree = Path(directory)
        node = worktree / "node"
        node.write_text(
            "#!/usr/bin/env python3\nimport json, sys\nprint(json.dumps(sys.argv[1:]))\n"
        )
        node.chmod(0o755)
        env = os.environ.copy()
        env["PATH"] = f"{worktree}{os.pathsep}{env.get('PATH', '')}"
        result = subprocess.run(
            (str(wrapper), *args),
            cwd=worktree,
            env=env,
            check=True,
            capture_output=True,
            text=True,
        )
        return json.loads(result.stdout)


compile(FETCHER.read_text(), FETCHER.name, "exec")
for command in (
    ("node", str(HELPER), "self-test"),
    ("sh", "-n", str(VERIFIER)),
):
    result = subprocess.run(command, cwd=ROOT)
    if result.returncode:
        raise SystemExit(result.returncode)

assert wrapper_args(FETCHER) == [str(HELPER), "fetch", "--json"]
assert wrapper_args(FETCHER, "53") == [str(HELPER), "fetch", "--pr", "53", "--json"]
assert wrapper_args(VERIFIER) == [str(HELPER), "target"]
assert wrapper_args(VERIFIER, "53") == [str(HELPER), "target", "--pr", "53"]
