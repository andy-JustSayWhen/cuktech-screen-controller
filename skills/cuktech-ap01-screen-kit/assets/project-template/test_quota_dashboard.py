import unittest
import os
import hashlib
import io
import json
from datetime import date, datetime
from pathlib import Path
from tempfile import TemporaryDirectory

from quota_dashboard import (
    AP01_GIF_MAX_BYTES,
    Quota,
    _claude_fable_limit,
    _codex_command,
    _codex_executable,
    _compact_reset_summary,
    _decrypt_windows_cookie,
    _format_tokens,
    _parse_codex_usage,
    _read_json_rpc,
    _reset_countdown,
    render_frame,
    render_master,
    render_outputs,
)


class QuotaDashboardTests(unittest.TestCase):
    def test_token_values_use_yi_units(self) -> None:
        self.assertEqual(_format_tokens(17_163_173_483), "171.6亿")
        self.assertEqual(_format_tokens(15_533_715_997), "155.3亿")
        self.assertEqual(_format_tokens(1_090_545_534), "10.9亿")
        self.assertEqual(_format_tokens(50_000_000), "0.5亿")
        self.assertEqual(_format_tokens(None), "暂无数据")

    def test_codex_usage_normalizes_today_and_last_30_days(self) -> None:
        usage = _parse_codex_usage(
            {
                "summary": {
                    "lifetimeTokens": 123_456,
                    "peakDailyTokens": 9_999,
                },
                "dailyUsageBuckets": [
                    {"startDate": "2026-07-21", "tokens": 100},
                    {"startDate": "2026-07-23", "tokens": 300},
                ],
            },
            date(2026, 7, 23),
        )
        self.assertEqual(usage["today_tokens"], 300)
        self.assertEqual(usage["last_30d_tokens"], 400)
        self.assertEqual(len(usage["daily_tokens"]), 30)
        self.assertEqual(usage["daily_tokens"][-2], ("2026-07-22", 0))
        self.assertEqual(usage["usage_as_of"], "2026-07-23")
        self.assertEqual(usage["lifetime_tokens"], 123_456)
        self.assertEqual(usage["peak_daily_tokens"], 9_999)

    def test_codex_usage_does_not_invent_missing_today(self) -> None:
        usage = _parse_codex_usage(
            {
                "dailyUsageBuckets": [
                    {"startDate": "2026-07-22", "tokens": 250},
                ]
            },
            date(2026, 7, 23),
        )
        self.assertIsNone(usage["today_tokens"])
        self.assertEqual(usage["last_30d_tokens"], 250)
        self.assertEqual(usage["usage_as_of"], "2026-07-22")

    def test_json_rpc_pipe_reader_is_windows_compatible(self) -> None:
        class Process:
            stdout = io.StringIO(
                json.dumps({"method": "ready"}) + "\n" + json.dumps({"id": 7, "result": {"ok": True}}) + "\n"
            )

        self.assertEqual(_read_json_rpc(Process(), 7, 1)["result"], {"ok": True})

    def test_windows_batch_codex_uses_cmd_prefix(self) -> None:
        from unittest.mock import patch

        with patch("quota_dashboard.os.name", "nt"), patch.dict(
            os.environ, {"COMSPEC": "C:/Windows/System32/cmd.exe"}
        ):
            self.assertEqual(
                _codex_command("C:/Users/Test/AppData/Roaming/npm/codex.cmd"),
                [
                    "C:/Windows/System32/cmd.exe",
                    "/d",
                    "/s",
                    "/c",
                    "C:/Users/Test/AppData/Roaming/npm/codex.cmd",
                ],
            )

    def test_windows_chromium_aes_cookie_decrypts_in_memory(self) -> None:
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM

        key = bytes(range(32))
        nonce = bytes(range(12))
        host = ".claude.ai"
        value = "sk-ant-session-test"
        plaintext = hashlib.sha256(host.encode()).digest() + value.encode()
        encrypted = b"v10" + nonce + AESGCM(key).encrypt(nonce, plaintext, None)
        self.assertEqual(_decrypt_windows_cookie(encrypted, host, key), value)

    def test_codex_executable_accepts_explicit_desktop_or_cli_path(self) -> None:
        from unittest.mock import patch

        with TemporaryDirectory() as directory:
            executable = Path(directory) / "codex"
            executable.write_text("#!/bin/sh\n", encoding="utf-8")
            executable.chmod(0o755)
            with patch.dict(os.environ, {"CUKTECH_CODEX_BIN": str(executable)}):
                self.assertEqual(_codex_executable(), str(executable))

    def test_codex_executable_finds_windows_store_companion_binary(self) -> None:
        from unittest.mock import patch

        with TemporaryDirectory() as directory:
            executable = Path(directory) / "OpenAI/Codex/bin/codex.exe"
            executable.parent.mkdir(parents=True)
            executable.write_bytes(b"MZ")
            executable.chmod(0o755)
            with patch.dict(
                os.environ,
                {"LOCALAPPDATA": directory, "CUKTECH_CODEX_BIN": ""},
            ), patch("quota_dashboard.shutil.which", return_value=None):
                self.assertEqual(_codex_executable(), str(executable))

    def test_fable_scoped_limit_is_kept_even_when_inactive(self) -> None:
        usage = {
            "limits": [
                {
                    "kind": "weekly_scoped",
                    "group": "weekly",
                    "percent": 37,
                    "resets_at": "2026-07-16T12:00:00+00:00",
                    "scope": {"model": {"id": None, "display_name": "Fable"}},
                    "is_active": False,
                }
            ]
        }
        used, reset, label = _claude_fable_limit(usage)
        self.assertEqual(used, 37.0)
        self.assertIsNotNone(reset)
        self.assertEqual(label, "FABLE 5")

    def test_reset_countdown_is_compact(self) -> None:
        now = datetime.fromtimestamp(1_000_000).astimezone()
        self.assertEqual(_reset_countdown(1_000_000 + 90_000, now), "RESET 1D 01H")
        self.assertEqual(_reset_countdown(None, now), "NOT STARTED")

    def test_reset_times_share_one_compact_chinese_header_line(self) -> None:
        five_reset = 1_784_203_199
        weekly_reset = 1_784_684_444
        five_target = datetime.fromtimestamp(five_reset).astimezone()
        week_target = datetime.fromtimestamp(weekly_reset).astimezone()
        weekday = "一二三四五六日"[week_target.weekday()]
        claude = Quota(
            provider="CLAUDE",
            used_percent=20,
            resets_at=five_reset,
            weekly_used_percent=40,
            weekly_resets_at=weekly_reset,
        )
        self.assertEqual(
            _compact_reset_summary(claude),
            f"5时{five_target:%H:%M}｜周{weekday}{week_target:%H:%M}",
        )
        codex = Quota(
            provider="CODEX",
            used_percent=None,
            weekly_used_percent=16,
            weekly_resets_at=weekly_reset,
        )
        self.assertEqual(
            _compact_reset_summary(codex),
            f"5时活动｜周{weekday}{week_target:%H:%M}",
        )

    def test_top_overlay_band_stays_empty(self) -> None:
        claude = Quota(
            provider="CLAUDE",
            used_percent=0,
            weekly_used_percent=50,
            fable_used_percent=25,
            fable_label="FABLE 5",
        )
        codex = Quota(provider="CODEX", used_percent=None, weekly_used_percent=10)
        image = render_frame(claude, codex)
        self.assertEqual(image.size, (320, 240))
        background = image.getpixel((0, 0))
        self.assertTrue(
            all(image.getpixel((x, y)) == background for y in range(40) for x in range(320))
        )

    def test_master_is_four_times_device_resolution(self) -> None:
        claude = Quota(provider="CLAUDE", used_percent=0, weekly_used_percent=100)
        codex = Quota(provider="CODEX", used_percent=None, weekly_used_percent=16)
        master = render_master(claude, codex)
        self.assertEqual(master.size, (1280, 960))
        background = master.getpixel((0, 0))
        self.assertTrue(
            all(master.getpixel((x, y)) == background for y in range(160) for x in range(1280))
        )

    def test_weekly_ring_renders_100_90_50_and_10_percent_states(self) -> None:
        claude = Quota(provider="CLAUDE", used_percent=None)
        cases = (
            (0, (36, 217, 247)),
            (10, (36, 217, 247)),
            (50, (255, 155, 66)),
            (90, (255, 92, 69)),
        )
        frames = []
        for used, expected_accent in cases:
            frame = render_frame(
                claude,
                Quota(provider="CODEX", used_percent=None, weekly_used_percent=used),
            )
            self.assertIn(expected_accent, set(frame.get_flattened_data()))
            frames.append(frame.tobytes())
        self.assertEqual(len(set(frames)), 4)

    def test_token_visualizations_change_with_daily_usage(self) -> None:
        claude = Quota(provider="CLAUDE", used_percent=None)
        low = Quota(
            provider="CODEX",
            used_percent=None,
            weekly_used_percent=20,
            today_tokens=100,
            last_30d_tokens=700,
            daily_tokens=tuple((f"2026-07-{day:02d}", 100) for day in range(17, 24)),
        )
        high = Quota(
            provider="CODEX",
            used_percent=None,
            weekly_used_percent=20,
            today_tokens=700,
            last_30d_tokens=2_800,
            daily_tokens=tuple(
                (f"2026-07-{day:02d}", (day - 16) * 100) for day in range(17, 24)
            ),
        )
        self.assertNotEqual(
            render_frame(claude, low).crop((149, 56, 313, 199)).tobytes(),
            render_frame(claude, high).crop((149, 56, 313, 199)).tobytes(),
        )

    def test_ap01_gif_uses_verified_animation_container(self) -> None:
        from PIL import Image

        claude = Quota(provider="CLAUDE", used_percent=0, weekly_used_percent=100)
        codex = Quota(provider="CODEX", used_percent=None, weekly_used_percent=16)
        with TemporaryDirectory() as directory:
            root = Path(directory)
            gif_path = root / "screen.gif"
            render_outputs(
                claude,
                codex,
                root / "screen.png",
                gif_path,
                root / "master.png",
                root / "screen@2x.png",
            )
            with Image.open(gif_path) as image:
                self.assertEqual(image.info.get("version"), b"GIF89a")
                self.assertEqual(image.info.get("loop"), 0)
                self.assertEqual(image.info.get("duration"), 600)
                self.assertEqual(image.n_frames, 4)
            self.assertLessEqual(gif_path.stat().st_size, AP01_GIF_MAX_BYTES)
            self.assertLessEqual(gif_path.stat().st_size, 90_000)
            with Image.open(root / "screen@2x.png") as preview:
                self.assertEqual(preview.size, (640, 480))


if __name__ == "__main__":
    unittest.main()
