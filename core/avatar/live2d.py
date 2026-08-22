from __future__ import annotations

from .models import (
    AvatarExpression,
    AvatarMotion,
    LipSyncData,
)


class Live2DController:
    """
    Live2D角色控制。
    """

    def speak(
        self,
        lip_sync: LipSyncData,
    ):
        return {
            "type": "live2d_lipsync",
            "audio": lip_sync.audio_path,
        }


    def expression(
        self,
        data: AvatarExpression,
    ):
        return {
            "expression": data.emotion,
        }


    def motion(
        self,
        data: AvatarMotion,
    ):
        return {
            "motion": data.action,
        }
