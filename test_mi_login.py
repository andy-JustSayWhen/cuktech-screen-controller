from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import mi_cloud
from local_env import read_env_file, update_env_file
from mi_cloud import MiCloud
from mi_login import XiaomiQrLogin


class FakeResponse:
    def __init__(self, *, text: str = "", content: bytes = b"", status: int = 200) -> None:
        self.text = text
        self.content = content
        self.status_code = status

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")


class FakeSession:
    def __init__(self, responses: list[FakeResponse]) -> None:
        self.headers: dict[str, str] = {}
        self.responses = responses

    def get(self, *args, **kwargs) -> FakeResponse:
        return self.responses.pop(0)


class XiaomiQrLoginTests(unittest.TestCase):
    def test_qr_login_returns_only_reusable_env_values(self) -> None:
        responses = [
            FakeResponse(
                text=(
                    '&&&START&&&{"qr":"https://example.test/qr",'
                    '"loginUrl":"https://example.test/login",'
                    '"lp":"https://example.test/poll","timeout":60}'
                )
            ),
            FakeResponse(content=b"PNG"),
            FakeResponse(text='&&&START&&&{"userId":"10001","passToken":"secret"}'),
        ]
        session = FakeSession(responses)
        with tempfile.TemporaryDirectory() as directory:
            qr = Path(directory) / "login.png"
            login = XiaomiQrLogin(session=session)
            challenge = login.start(qr, 30)
            result = login.wait(challenge)
            self.assertEqual(qr.read_bytes(), b"PNG")
            self.assertEqual(result["CUKTECH_MI_USER_ID"], "10001")
            self.assertEqual(result["CUKTECH_MI_PASS_TOKEN"], "secret")
            self.assertEqual(len(result["CUKTECH_MI_DEVICE_ID"]), 16)

    def test_env_update_preserves_device_values_and_uses_mode_600(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / ".env"
            path.write_text(
                "# existing\nCUKTECH_AP01_IP=192.168.1.2\nCUKTECH_MI_USER_ID=old\n",
                encoding="utf-8",
            )
            update_env_file(
                path,
                {
                    "CUKTECH_MI_USER_ID": "10001",
                    "CUKTECH_MI_PASS_TOKEN": "secret",
                },
            )
            values = read_env_file(path)
            self.assertEqual(values["CUKTECH_AP01_IP"], "192.168.1.2")
            self.assertEqual(values["CUKTECH_MI_USER_ID"], "10001")
            self.assertEqual(values["CUKTECH_MI_PASS_TOKEN"], "secret")
            self.assertEqual(path.stat().st_mode & 0o777, 0o600)

    def test_micloud_falls_back_to_project_env_file(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / ".env"
            update_env_file(
                path,
                {
                    "CUKTECH_MI_USER_ID": "10001",
                    "CUKTECH_MI_PASS_TOKEN": "secret",
                    "CUKTECH_MI_DEVICE_ID": "device",
                },
            )
            with (
                patch.object(mi_cloud, "DEFAULT_ENV", path),
                patch.dict(
                    os.environ,
                    {
                        "CUKTECH_MI_USER_ID": "",
                        "CUKTECH_MI_PASS_TOKEN": "",
                        "CUKTECH_MI_DEVICE_ID": "",
                        "CUKTECH_MI_CREDENTIALS": "",
                    },
                ),
            ):
                self.assertEqual(
                    MiCloud._load_account(),
                    {
                        "userId": "10001",
                        "passToken": "secret",
                        "deviceId": "device",
                    },
                )


if __name__ == "__main__":
    unittest.main()
