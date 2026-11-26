"""Exercise the foreground launcher without a Tailscale dependency in CI."""

import json
import unittest
from unittest.mock import patch

import run


class PreviewLauncherTest(unittest.TestCase):
    def test_replaces_bind_argument_and_preserves_server_arguments(self):
        state = {"BackendState": "Running", "Self": {"TailscaleIPs": ["fd7a::1", "100.64.0.1"]}}
        with patch.object(run.subprocess, "check_output", return_value=json.dumps(state)), patch.object(run.os, "execvp") as execute:
            run.main(["serve", "--host", "{host}", "dir with spaces"])
            execute.assert_called_once_with("serve", ["serve", "--host", "100.64.0.1", "dir with spaces"])

    def test_stopped_tailnet_blocks_launch(self):
        with patch.object(run.subprocess, "check_output", return_value='{"BackendState":"Stopped"}'), patch.object(run.os, "execvp") as execute:
            with self.assertRaisesRegex(SystemExit, "Start Tailscale"):
                run.main(["serve", "--host", "{host}"])
            execute.assert_not_called()


if __name__ == "__main__":
    unittest.main()
