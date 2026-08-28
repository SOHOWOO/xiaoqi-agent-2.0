"""小七 · 配置管理（ConfigManager）

统一管理 AI / 语音 / 记忆 / LifeLoop / UI / 系统设置。
配置文件：%APPDATA%/xiaoqi/config.json（用户目录，升级不丢）。
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .paths import get_config_path

DEFAULTS: dict[str, Any] = {
    "setup_complete": False,
    "ai": {
        "provider": "deepseek",
        "base_url": "https://api.deepseek.com",
        "model": "deepseek-v4-flash",
        "temperature": 0.7,
        "max_tokens": 1024,
    },
    "tts": {
        "provider": "alibaba",
        "model": "qwen3-tts-flash",
        "voice_id": "",
        "region": "singapore",
        "language": "Chinese",
    },
    "stt": {
        "provider": "browser",
        "language": "zh-CN",
    },
    "avatar": {
        "mode": "three",
        "vrm_url": "/assets/avatar/xiaoqi.vrm",
    },
    "ui": {
        "night_mode": False,
        "sound": False,
        "show_hud": False,
        "allow_proactive": True,
    },
    "life": {
        "sim_minutes_per_real_second": 60,
    },
    "system": {
        "auto_voice": False,
    },
}


class ConfigManager:
    """应用配置读写（分层合并默认值）。"""

    def __init__(self, path: Path | None = None) -> None:
        self.path = path or get_config_path()
        self._data: dict = {}
        self._load()

    def _load(self) -> None:
        if not self.path.is_file():
            self._data = json.loads(json.dumps(DEFAULTS))
            return
        try:
            loaded = json.loads(self.path.read_text(encoding="utf-8"))
            self._data = self._merge(DEFAULTS, loaded)
        except (json.JSONDecodeError, OSError):
            self._data = json.loads(json.dumps(DEFAULTS))

    @staticmethod
    def _merge(base: dict, override: dict) -> dict:
        result = dict(base)
        for key, value in override.items():
            if isinstance(value, dict) and isinstance(result.get(key), dict):
                result[key] = ConfigManager._merge(result[key], value)
            else:
                result[key] = value
        return result

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(
            json.dumps(self._data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def get(self, section: str, key: str, default: Any = None) -> Any:
        return self._data.get(section, {}).get(key, default)

    def set(self, section: str, key: str, value: Any) -> None:
        if section not in self._data:
            self._data[section] = {}
        self._data[section][key] = value
        self.save()

    def section(self, name: str) -> dict:
        return dict(self._data.get(name, {}))

    def all(self) -> dict:
        return json.loads(json.dumps(self._data))

    @property
    def setup_complete(self) -> bool:
        return bool(self._data.get("setup_complete", False))

    def mark_setup_complete(self) -> None:
        self._data["setup_complete"] = True
        self.save()
