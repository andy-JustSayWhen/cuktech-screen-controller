from __future__ import annotations

import os
import unittest
from unittest.mock import patch

import ap01_screen_bridge
import ap01_wifi_bridge


class PlatformSupportTests(unittest.TestCase):
    def test_static_bridge_accepts_explicit_cross_platform_lan_ip(self) -> None:
        with patch.dict(os.environ, {"AP01_LAN_IP": "192.168.50.20"}):
            self.assertEqual(ap01_screen_bridge.lan_ip(), "192.168.50.20")

    def test_quota_bridge_accepts_explicit_cross_platform_lan_ip(self) -> None:
        with patch.dict(os.environ, {"AP01_LAN_IP": "10.10.0.8"}):
            self.assertEqual(ap01_wifi_bridge.lan_ip(), "10.10.0.8")

    def test_invalid_override_is_ignored(self) -> None:
        with (
            patch.dict(os.environ, {"AP01_LAN_IP": "not-an-ip"}),
            patch("ap01_screen_bridge.subprocess.run", side_effect=OSError),
            patch("ap01_screen_bridge.socket.socket") as socket_factory,
            patch(
                "ap01_screen_bridge.socket.getaddrinfo",
                return_value=[(2, 1, 6, "", ("192.168.9.5", 0))],
            ),
        ):
            socket_factory.return_value.getsockname.side_effect = OSError
            self.assertEqual(ap01_screen_bridge.lan_ip(), "192.168.9.5")


if __name__ == "__main__":
    unittest.main()
