"""小七 · VoiceProfile（声音克隆配置）

一个 profile = 一种声音。
替换 reference_audio / 配置即可换声音，无需改代码。
真人声音素材不提交 GitHub，仅记录引用路径。
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

DEFAULT_PROFILE_DIR = Path(__file__).parent / "profiles"
DEFAULT_PROFILE = "xiaoqi"


@dataclass(frozen=True)
class VoiceProfile:
    name: str
    provider: str = "alibaba"
    voice_id: str = ""
    reference_audio: str = ""
    language: str = "zh"
    speed: float = 1.0
    pitch: float = 0.0
    emotion: str = "neutral"
    extra: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "provider": self.provider,
            "voice_id": self.voice_id,
            "reference_audio": self.reference_audio,
            "language": self.language,
            "speed": self.speed,
            "pitch": self.pitch,
            "emotion": self.emotion,
            "has_reference": bool(self.reference_audio),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "VoiceProfile":
        return cls(
            name=str(data.get("name", DEFAULT_PROFILE)),
            provider=str(data.get("provider", "alibaba")),
            voice_id=str(data.get("voice_id", "")),
            reference_audio=str(data.get("reference_audio", "")),
            language=str(data.get("language", "zh")),
            speed=float(data.get("speed", 1.0)),
            pitch=float(data.get("pitch", 0.0)),
            emotion=str(data.get("emotion", "neutral")),
            extra={
                k: v
                for k, v in data.items()
                if k
                not in {
                    "name",
                    "provider",
                    "voice_id",
                    "reference_audio",
                    "language",
                    "speed",
                    "pitch",
                    "emotion",
                }
            },
        )


def _resolve_reference(profile_dir: Path, reference: str) -> str:
    """把相对路径解析为绝对路径；原样保留绝对路径。"""

    ref = Path(reference)

    if ref.is_absolute():
        return str(ref)

    return str((profile_dir / ref).resolve())


def load_profile(
    name: str = DEFAULT_PROFILE,
    profile_dir: Path | str | None = None,
) -> VoiceProfile | None:
    """按名称加载 profile；不存在返回 None。"""

    directory = Path(profile_dir) if profile_dir else DEFAULT_PROFILE_DIR

    path = directory / name / "profile.json"

    if not path.is_file():
        return None

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None

    data.setdefault("name", name)

    if data.get("reference_audio"):
        data["reference_audio"] = _resolve_reference(
            path.parent,
            data["reference_audio"],
        )

    return VoiceProfile.from_dict(data)


def active_profile_name() -> str:
    return os.getenv("XIAOQI_VOICE_PROFILE", DEFAULT_PROFILE)


def get_active_profile() -> VoiceProfile | None:
    return load_profile(active_profile_name())
