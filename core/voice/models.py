from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AudioRequest:
    """
    文本转语音请求。
    """

    text: str

    voice_id: str | None = None

    language: str = "zh"


@dataclass(frozen=True)
class AudioResponse:
    """
    生成后的音频。
    """

    audio_path: str

    sample_rate: int = 24000
