from __future__ import annotations

from ..models import AudioInput


class FastRTCInput:
    """
    实时音频流入口。

    负责:
    microphone
       ↓
    websocket/webrtc
       ↓
    AudioInput
    """

    def __init__(
        self,
        callback,
    ):
        self.callback = callback


    def receive(
        self,
        data: bytes,
    ):

        audio = AudioInput(
            data=data,
            format="pcm",
        )

        return self.callback(
            audio
        )
