from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AudioChunk:
    """
    实时音频片段。
    """

    data: bytes

    sample_rate: int = 16000



@dataclass(frozen=True)
class Transcript:
    """
    语音识别结果。
    """

    text: str

    final: bool = True
