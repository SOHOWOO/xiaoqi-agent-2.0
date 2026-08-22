from __future__ import annotations

from typing import Protocol, runtime_checkable

from .models import (
    AudioChunk,
    Transcript,
)


@runtime_checkable
class SpeechRecognizer(Protocol):
    """
    语音识别接口。

    后续接：
    - Whisper
    - faster-whisper
    - Whisper.cpp
    """

    def transcribe(
        self,
        audio: AudioChunk,
    ) -> Transcript:
        ...
