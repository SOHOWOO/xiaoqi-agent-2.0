from __future__ import annotations

from typing import Protocol, runtime_checkable

from .models import (
    AvatarExpression,
    AvatarMotion,
    LipSyncData,
)


@runtime_checkable
class AvatarProvider(Protocol):
    """
    小七角色驱动接口。
    """

    def speak(
        self,
        lip_sync: LipSyncData,
    ):
        ...


    def expression(
        self,
        data: AvatarExpression,
    ):
        ...


    def motion(
        self,
        data: AvatarMotion,
    ):
        ...
