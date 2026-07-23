#!/usr/bin/env python3
"""Log into Xiaomi Cloud with a QR code and persist only reusable credentials."""

from __future__ import annotations

import argparse
import json
import os
import secrets
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import requests

from local_env import update_env_file
from mi_cloud import MODEL, MiCloud


HERE = Path(__file__).resolve().parent
DEFAULT_ENV = HERE / ".env"
DEFAULT_QR = HERE / "artifacts" / "xiaomi-login-qr.png"
LOGIN_ENDPOINT = "https://account.xiaomi.com/longPolling/loginUrl"
USER_AGENT = "APP/com.xiaomi.mihome APPV/10.5.201"


def xiaomi_json(text: str) -> dict[str, Any]:
    payload = text.removeprefix("&&&START&&&")
    value = json.loads(payload)
    if not isinstance(value, dict):
        raise RuntimeError("小米登录响应不是对象")
    return value


@dataclass(frozen=True)
class LoginChallenge:
    qr_url: str
    login_url: str
    polling_url: str
    timeout: float


class XiaomiQrLogin:
    def __init__(self, session: requests.Session | None = None) -> None:
        self.session = session or requests.Session()
        self.session.headers["User-Agent"] = USER_AGENT

    def start(self, qr_output: Path, requested_timeout: float) -> LoginChallenge:
        response = self.session.get(
            LOGIN_ENDPOINT,
            params={
                "_qrsize": "480",
                "qs": "%3Fsid%3Dxiaomiio%26_json%3Dtrue",
                "callback": "https://sts.api.io.mi.com/sts",
                "_hasLogo": "false",
                "sid": "xiaomiio",
                "serviceParam": "",
                "_locale": "zh_CN",
                "_dc": str(int(time.time() * 1000)),
            },
            timeout=20,
        )
        response.raise_for_status()
        payload = xiaomi_json(response.text)
        required = ("qr", "loginUrl", "lp")
        if any(not payload.get(key) for key in required):
            raise RuntimeError("小米没有返回完整的二维码登录信息")
        server_timeout = float(payload.get("timeout") or requested_timeout)
        challenge = LoginChallenge(
            qr_url=str(payload["qr"]),
            login_url=str(payload["loginUrl"]),
            polling_url=str(payload["lp"]),
            timeout=min(requested_timeout, server_timeout),
        )

        image = self.session.get(challenge.qr_url, timeout=20)
        image.raise_for_status()
        qr_output.parent.mkdir(parents=True, exist_ok=True)
        temporary = qr_output.with_name(f".{qr_output.name}.{secrets.token_hex(4)}")
        try:
            temporary.write_bytes(image.content)
            os.chmod(temporary, 0o600)
            os.replace(temporary, qr_output)
            os.chmod(qr_output, 0o600)
        finally:
            temporary.unlink(missing_ok=True)
        return challenge

    def wait(self, challenge: LoginChallenge) -> dict[str, str]:
        started = time.monotonic()
        while time.monotonic() - started < challenge.timeout:
            remaining = challenge.timeout - (time.monotonic() - started)
            try:
                response = self.session.get(
                    challenge.polling_url,
                    timeout=max(1.0, min(10.0, remaining)),
                )
            except requests.Timeout:
                continue
            if response.status_code != 200:
                time.sleep(0.5)
                continue
            payload = xiaomi_json(response.text)
            user_id = str(payload.get("userId") or "").strip()
            pass_token = str(payload.get("passToken") or "").strip()
            if user_id and pass_token:
                return {
                    "CUKTECH_MI_USER_ID": user_id,
                    "CUKTECH_MI_PASS_TOKEN": pass_token,
                    "CUKTECH_MI_DEVICE_ID": secrets.token_hex(8).upper(),
                }
        raise TimeoutError("二维码已超时，请重新生成后扫码")


def verify_ap01(credentials: dict[str, str]) -> dict[str, Any]:
    previous = {key: os.environ.get(key) for key in credentials}
    os.environ.update(credentials)
    try:
        device = MiCloud().ap01()
    finally:
        for key, value in previous.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value
    return device


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--env-file", type=Path, default=DEFAULT_ENV)
    parser.add_argument("--qr-output", type=Path, default=DEFAULT_QR)
    parser.add_argument("--timeout", type=float, default=300)
    parser.add_argument(
        "--skip-device-check",
        action="store_true",
        help="只保存登录态，不检查账号中是否存在 AP01",
    )
    args = parser.parse_args()

    login = XiaomiQrLogin()
    challenge = login.start(args.qr_output, args.timeout)
    print(f"二维码已生成：{args.qr_output.resolve()}", flush=True)
    print("请使用拥有目标 AP01 的小米账号扫码并在手机上确认登录。", flush=True)
    credentials = login.wait(challenge)
    print("扫码确认成功，正在验证账号中的 AP01…", flush=True)

    device: dict[str, Any] | None = None
    if not args.skip_device_check:
        device = verify_ap01(credentials)
        if str(device.get("model") or "") != MODEL:
            raise RuntimeError("登录账号返回的设备型号不是受支持的 AP01")
    update_env_file(args.env_file, credentials)
    print(f"登录态已保存到 {args.env_file.resolve()}，文件权限为 600。", flush=True)
    if device is not None:
        print(
            "已确认目标设备："
            f"model={device.get('model')} "
            f"firmware={device.get('fw_version')} "
            f"online={device.get('isOnline')}",
            flush=True,
        )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (RuntimeError, TimeoutError, ValueError, requests.RequestException) as exc:
        print(f"登录失败：{exc}", file=sys.stderr)
        raise SystemExit(1)
