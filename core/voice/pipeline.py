from __future__ import annotations

from .models import (
    AudioInput,
    AudioOutput,
)
from .provider import (
    SpeechRecognizer,
    SpeechSynthesizer,
)


class VoicePipeline:
    """
    语音输入输出流程。
    """

    def __init__(
        self,
        asr: SpeechRecognizer,
        tts: SpeechSynthesizer,
    ):
        self.asr = asr
        self.tts = tts

    def listen(
        self,
        audio: AudioInput,
    ) -> str:
        return self.asr.transcribe(audio)

    def speak(
        self,
        text: str,
    ) -> AudioOutput:
        return self.tts.synthesize(text)
