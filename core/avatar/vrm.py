from __future__ import annotations

from .models import (
    AvatarExpression,
    AvatarMotion,
    LipSyncData,
)


class VRMController:
    """
    VRM模型控制。

    后续连接：
    - UniVRM
    - Three.js VRM
    - Unity
    """

    def speak(
        self,
        lip_sync: LipSyncData,
    ):
        return {
            "type": "vrm_lipsync",
            "audio": lip_sync.audio_path,
        }


    def expression(
        self,
        data: AvatarExpression,
    ):
        return {
            "emotion": data.emotion,
            "intensity": data.intensity,
        }


    def motion(
        self,
        data: AvatarMotion,
    ):
        return {
            "motion": data.action,
        }
