from __future__ import annotations

from ..models import AudioInput


class WhisperRecognizer:
    """
    Whisper ASR适配器。

    后续可接:
    - openai-whisper
    - faster-whisper
    - whisper.cpp
    - FastRTC
    """

    def __init__(
        self,
        model=None,
    ):
        self.model = model


    def transcribe(
        self,
        audio: AudioInput,
    ) -> str:

        if self.model is None:
            raise RuntimeError(
                "Whisper model is not configured"
            )

        result = self.model.transcribe(
            audio.data
        )

        if isinstance(result, dict):
            return result.get(
                "text",
                ""
            )

        return str(result)
