from __future__ import annotations

from typing import Protocol, runtime_checkable

from .models import (
    AudioRequest,
    AudioResponse,
)


@runtime_checkable
class TTSProvider(Protocol):
    """
    小七统一语音生成接口。
    """

    def generate(
        self,
        request: AudioRequest,
    ) -> AudioResponse:
        ...
