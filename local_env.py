#!/usr/bin/env python3
"""Small, dependency-free helpers for the project's private .env file."""

from __future__ import annotations

import os
import re
import shlex
import tempfile
from pathlib import Path
from typing import Mapping


KEY_PATTERN = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def read_env_file(path: Path) -> dict[str, str]:
    """Read shell-style KEY=VALUE lines without evaluating shell code."""

    if not path.exists():
        return {}
    values: dict[str, str] = {}
    for original in path.read_text(encoding="utf-8-sig").splitlines():
        line = original.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[7:].lstrip()
        key, separator, raw_value = line.partition("=")
        key = key.strip()
        if not separator or not KEY_PATTERN.fullmatch(key):
            continue
        lexer = shlex.shlex(raw_value, posix=True)
        lexer.whitespace_split = True
        lexer.commenters = ""
        parsed = list(lexer)
        if len(parsed) <= 1:
            values[key] = parsed[0] if parsed else ""
    return values


def update_env_file(path: Path, updates: Mapping[str, str]) -> None:
    """Atomically update selected values while preserving unrelated lines."""

    for key, value in updates.items():
        if not KEY_PATTERN.fullmatch(key):
            raise ValueError(f"无效的 .env 变量名：{key}")
        if "\n" in value or "\r" in value:
            raise ValueError(f".env 变量 {key} 不能包含换行")

    path.parent.mkdir(parents=True, exist_ok=True)
    lines = path.read_text(encoding="utf-8-sig").splitlines() if path.exists() else []
    rendered: list[str] = []
    remaining = dict(updates)
    seen: set[str] = set()
    for original in lines:
        candidate = original.strip()
        if candidate.startswith("export "):
            candidate = candidate[7:].lstrip()
        key, separator, _ = candidate.partition("=")
        key = key.strip()
        if separator and key in updates:
            if key not in seen:
                rendered.append(f"{key}={shlex.quote(updates[key])}")
                seen.add(key)
                remaining.pop(key, None)
            continue
        rendered.append(original)
    if rendered and rendered[-1]:
        rendered.append("")
    rendered.extend(f"{key}={shlex.quote(value)}" for key, value in remaining.items())
    content = "\n".join(rendered).rstrip("\n") + "\n"

    temporary_name = ""
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=path.parent,
            prefix=f".{path.name}.",
            delete=False,
        ) as stream:
            temporary_name = stream.name
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        os.chmod(temporary_name, 0o600)
        os.replace(temporary_name, path)
        os.chmod(path, 0o600)
    finally:
        if temporary_name and os.path.exists(temporary_name):
            os.unlink(temporary_name)
