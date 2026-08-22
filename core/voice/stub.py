from __future__ import annotations

from .models import (
    AudioRequest,
    AudioResponse,
)


class StubTTSProvider:
    """
    本地测试语音。
    """

    def generate(
        self,
        request: AudioRequest,
    ) -> AudioResponse:

        return AudioResponse(
            audio_path="stub.wav",
        )
