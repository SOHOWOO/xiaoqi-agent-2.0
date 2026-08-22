from __future__ import annotations

from typing import Protocol

from .models import AudioChunk


class AudioStream(Protocol):
    """
    实时音频输入。

    后续接：
    - FastRTC
    - WebRTC
    """

    def receive(
        self,
    ) -> AudioChunk:
        ...
