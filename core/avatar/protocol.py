from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass(frozen=True)
class AvatarEmotion:
    """Avatar 表现的情绪。"""

    name: str
    intensity: float = 1.0

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "intensity": round(self.intensity, 4),
        }


@dataclass(frozen=True)
class AvatarAction:
    """Avatar 执行的动作。"""

    name: str
    intensity: float = 1.0

    def to_dict(self) -> dict:
        return {
            "name": self.name,
        }


@dataclass(frozen=True)
class AvatarVoice:
    """Avatar 语音状态（嘴型同步由 Open-LLM-VTuber 负责）。"""

    speaking: bool = False

    def to_dict(self) -> dict:
        return {
            "speaking": self.speaking,
        }


@dataclass(frozen=True)
class AvatarEvent:
    """Avatar 状态事件（xiaoqi-agent -> Soul-of-Waifu）。"""

    type: str = "avatar_state"
    time: Optional[datetime] = None
    emotion: AvatarEmotion = field(
        default_factory=lambda: AvatarEmotion("calm")
    )
    action: AvatarAction = field(
        default_factory=lambda: AvatarAction("idle")
    )
    voice: AvatarVoice = field(
        default_factory=AvatarVoice
    )

    def to_dict(self) -> dict:
        return {
            "type": self.type,
            "time": (
                self.time.isoformat()
                if self.time is not None
                else None
            ),
            "emotion": self.emotion.to_dict(),
            "action": self.action.to_dict(),
            "voice": self.voice.to_dict(),
        }
