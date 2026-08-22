from __future__ import annotations

from .models import (
    AudioChunk,
    Transcript,
)


class StubSpeechRecognizer:
    """
    本地测试识别器。
    """

    def transcribe(
        self,
        audio: AudioChunk,
    ) -> Transcript:

        return Transcript(
            text="你好，小七"
        )
