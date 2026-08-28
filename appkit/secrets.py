"""小七 · API Key 安全存储

- 存于 %APPDATA%/xiaoqi/secrets.json（用户目录，非程序目录）
- Windows 上设置 ACL 仅当前用户可读写
- 值做简单混淆（非真实加密，防误读/防日志扫描）
- 绝不写入 Git / JS / HTML / EXE / 日志 / API 返回

注意：这是"权限 + 混淆"方案，不是强加密。
如需强加密可后续接 Windows Credential Manager。
"""

from __future__ import annotations

import base64
import json
import os
from pathlib import Path
from typing import Optional

from .paths import get_secrets_path

_MASK = b"xiaoqi-secrets-v1"


def _obfuscate(value: str) -> str:
    data = value.encode("utf-8")
    masked = bytes(b ^ _MASK[i % len(_MASK)] for i, b in enumerate(data))
    return base64.b64encode(masked).decode("ascii")


def _deobfuscate(value: str) -> str:
    try:
        masked = base64.b64decode(value.encode("ascii"))
    except Exception:
        return ""
    data = bytes(b ^ _MASK[i % len(_MASK)] for i, b in enumerate(masked))
    return data.decode("utf-8")


def _restrict_file(path: Path) -> None:
    """Windows ACL：仅当前用户可读写。"""

    if os.name != "nt":
        return

    try:
        import subprocess

        user = os.environ.get("USERNAME", "")
        if not user:
            return

        cmd = (
            f'icacls "{path}" /inheritance:r /grant:r '
            f'"{user}":(R,W) /quiet'
        )
        subprocess.run(
            cmd,
            shell=True,
            check=False,
            capture_output=True,
            timeout=10,
        )
    except Exception:
        pass


class SecretStore:
    """加载 / 保存 / 删除 API Key。"""

    KEYS = {
        "deepseek": "XIAOQI_LLM_API_KEY",
        "alibaba": "XIAOQI_ALIBABA_API_KEY",
        "openai": "OPENAI_API_KEY",
    }

    def __init__(self, path: Path | str | None = None) -> None:
        self.path = Path(path) if path else get_secrets_path()
        self._data: dict[str, str] = {}
        self._load()

    def _load(self) -> None:
        if not self.path.is_file():
            return
        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
            self._data = {
                k: _deobfuscate(v)
                for k, v in raw.items()
            }
        except (json.JSONDecodeError, OSError, UnicodeDecodeError):
            self._data = {}

    def _save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            k: _obfuscate(v)
            for k, v in self._data.items()
        }
        self.path.write_text(
            json.dumps(payload),
            encoding="utf-8",
        )
        _restrict_file(self.path)

    def get(self, provider: str) -> str:
        return self._data.get(provider, "")

    def set(self, provider: str, value: str) -> None:
        value = (value or "").strip()
        if value:
            self._data[provider] = value
        else:
            self._data.pop(provider, None)
        self._save()

    def delete(self, provider: str) -> None:
        self._data.pop(provider, None)
        self._save()

    def has(self, provider: str) -> bool:
        return bool(self._data.get(provider, ""))

    def configured_providers(self) -> list[str]:
        return [k for k, v in self._data.items() if v]

    def env_overrides(self) -> dict[str, str]:
        """返回可直接写入 os.environ 的映射。"""

        return {
            env: self._data.get(provider, "")
            for provider, env in self.KEYS.items()
        }


def load_secret(provider: str) -> str:
    return SecretStore().get(provider)


def save_secret(provider: str, value: str) -> None:
    SecretStore().set(provider, value)


def has_secret(provider: str) -> bool:
    return SecretStore().has(provider)
