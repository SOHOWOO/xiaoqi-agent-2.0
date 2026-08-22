from __future__ import annotations

from .provider import TTSProvider
from .models import (
    AudioRequest,
    AudioResponse,
)


class VoiceCloneEngine:
    """
    声音克隆统一入口。

    后续接：
    - GPT-SoVITS
    - CosyVoice
    - XTTS-v2
    """

    def __init__(
        self,
        provider: TTSProvider,
    ):
        self.provider = provider


    def speak(
        self,
        text: str,
        voice_id: str = "xiaoqi",
    ) -> AudioResponse:

        request = AudioRequest(
            text=text,
            voice_id=voice_id,
        )

        return self.provider.generate(
            request
        )
