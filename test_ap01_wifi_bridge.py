from __future__ import annotations

import json
import os
import socket
import subprocess
import sys
import time
import unittest
import urllib.request
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import mock

import ap01_wifi_bridge as bridge
from quota_dashboard import Quota


class WiFiBridgeTests(unittest.TestCase):
    def test_refresh_keeps_codex_live_when_claude_is_unavailable(self) -> None:
        with TemporaryDirectory() as directory:
            artifacts = Path(directory)
            paths = {
                "ARTIFACTS": artifacts,
                "PNG": artifacts / "quota-dashboard.png",
                "GIF": artifacts / "quota-dashboard.gif",
                "MASTER": artifacts / "quota-dashboard-master.png",
                "JSON_OUT": artifacts / "quota-current.json",
            }
            codex = Quota(
                provider="CODEX",
                used_percent=None,
                weekly_used_percent=50.0,
                plan="PRO",
                source="test",
            )
            with (
                mock.patch.multiple(bridge, **paths),
                mock.patch.object(
                    bridge,
                    "fetch_claude_desktop",
                    side_effect=RuntimeError("not installed"),
                ),
                mock.patch.object(bridge, "fetch_codex", return_value=codex),
                mock.patch.object(bridge.time, "sleep"),
            ):
                document = bridge.refresh()

            self.assertEqual(document["codex"]["weekly_used_percent"], 50.0)
            self.assertEqual(document["claude"]["source"], "unavailable")
            self.assertIn("warnings", document)
            self.assertTrue(paths["GIF"].read_bytes().startswith(b"GIF89a"))

    def test_bridge_serves_health_and_placeholder_before_live_refresh(self) -> None:
        root = Path(__file__).resolve().parent
        with TemporaryDirectory() as directory:
            try:
                with socket.socket() as sock:
                    sock.bind(("127.0.0.1", 0))
                    port = sock.getsockname()[1]
            except PermissionError:
                self.skipTest("local listening sockets are disabled in this sandbox")

            env = os.environ.copy()
            env["CUKTECH_ARTIFACTS_DIR"] = directory
            process = subprocess.Popen(
                [
                    sys.executable,
                    str(root / "ap01_wifi_bridge.py"),
                    "--bind",
                    "127.0.0.1",
                    "--port",
                    str(port),
                    "--interval",
                    "600",
                    "--no-initial-refresh",
                ],
                cwd=root,
                env=env,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
                text=True,
            )
            try:
                opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
                deadline = time.monotonic() + 8
                health = None
                while time.monotonic() < deadline:
                    try:
                        with opener.open(f"http://127.0.0.1:{port}/health", timeout=1) as response:
                            health = json.load(response)
                        break
                    except OSError:
                        time.sleep(0.1)
                self.assertIsNotNone(health, process.stderr.read() if process.poll() is not None else "")
                self.assertTrue(health["snapshot_ready"])

                with opener.open(f"http://127.0.0.1:{port}/screen.gif", timeout=2) as response:
                    payload = response.read()
                self.assertTrue(payload.startswith(b"GIF89a"))
                self.assertLessEqual(len(payload), 90_000)
            finally:
                process.terminate()
                try:
                    process.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait(timeout=3)
                if process.stderr is not None:
                    process.stderr.close()


if __name__ == "__main__":
    unittest.main()
