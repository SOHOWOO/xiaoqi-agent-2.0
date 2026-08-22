from __future__ import annotations

from .models import (
    LipSyncData,
    AvatarExpression,
    AvatarMotion,
)


class AvatarEngine:
    """
    小七数字人控制核心。
    """

    def __init__(
        self,
        provider,
    ):
        self.provider = provider


    def play_voice(
        self,
        audio_path: str,
    ):
        return self.provider.speak(
            LipSyncData(
                audio_path=audio_path
            )
        )


    def set_expression(
        self,
        emotion: str,
    ):
        return self.provider.expression(
            AvatarExpression(
                emotion=emotion
            )
        )


    def play_motion(
        self,
        action: str,
    ):
        return self.provider.motion(
            AvatarMotion(
                action=action
            )
        )
