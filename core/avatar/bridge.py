from __future__ import annotations

from .models import (
    AvatarCommand,
    AvatarEmotion,
)


class AvatarBridge:
    """
    将AI回复转换为Avatar行为。
    """

    def build_command(
        self,
        text: str,
        emotion: str = "neutral",
    ) -> AvatarCommand:

        return AvatarCommand(
            text=text,
            emotion=AvatarEmotion(
                name=emotion,
                intensity=0.5,
            ),
        )
