from __future__ import annotations

from collections import deque
from datetime import datetime
from typing import Optional, Protocol

from .emotion_mapper import map_emotion
from .motion_mapper import map_action
from .protocol import (
    AvatarAction,
    AvatarEmotion,
    AvatarEvent,
    AvatarVoice,
)


class AvatarBridge(Protocol):
    """Avatar 事件发送通道（SoW / Live2D / VRM）。"""

    def send(self, event: AvatarEvent) -> None:
        ...


class CallbackAvatarBridge:
    """记录事件的桥（测试 / 观测用）。"""

    def __init__(self) -> None:
        self.events: list[AvatarEvent] = []

    def send(self, event: AvatarEvent) -> None:
        self.events.append(event)


class AvatarController:
    """Avatar 控制器。

    订阅 xiaoqi-bus 事件（state_update / proactive_triggered），
    把核心内部状态映射为 AvatarEvent 并发送给 Avatar 表现层。

    隔离原则：
    - 不 import life_loop，只通过事件总线通信
    - 只做"表达"，不改变任何核心状态
    """

    def __init__(
        self,
        event_bus,
        bridge: AvatarBridge | None = None,
        *,
        subscribe: bool = True,
    ) -> None:
        self.event_bus = event_bus
        self.bridge = (
            bridge
            if bridge is not None
            else CallbackAvatarBridge()
        )

        self._pending_actions: deque[str] = deque()
        self._speaking = False
        self._last_event: Optional[AvatarEvent] = None

        if subscribe:
            event_bus.subscribe(
                "state_update",
                self._on_state_update,
            )
            event_bus.subscribe(
                "proactive_triggered",
                self._on_proactive,
            )

    # ---------------------------------------------------------
    # 事件订阅
    # ---------------------------------------------------------

    def _on_state_update(
        self,
        data: dict | None,
    ) -> None:
        if not data:
            return

        emotion_name = data.get(
            "dominant_emotion",
            "calm",
        )

        emotion_dict = data.get("emotion", {})
        intensity = float(
            emotion_dict.get(emotion_name, 0.5)
        )

        action_name = self._pop_action()

        event = AvatarEvent(
            time=self._parse_time(data),
            emotion=AvatarEmotion(
                name=emotion_name,
                intensity=intensity,
            ),
            action=AvatarAction(name=action_name),
            voice=AvatarVoice(speaking=self._speaking),
        )

        self._last_event = event

        self.bridge.send(event)

    def _on_proactive(
        self,
        data: dict | None,
    ) -> None:
        if not data:
            return

        action = data.get("action")

        if action:
            self._pending_actions.append(
                map_action(action)
            )

    # ---------------------------------------------------------
    # 控制
    # ---------------------------------------------------------

    def set_speaking(
        self,
        speaking: bool,
    ) -> None:
        """由 Open-LLM-VTuber 的 TTS 状态驱动。"""

        self._speaking = speaking

    def _pop_action(self) -> str:
        if self._pending_actions:
            return self._pending_actions.popleft()

        return "idle"

    @staticmethod
    def _parse_time(data: dict) -> Optional[datetime]:
        raw = data.get("simulated_time")

        if raw:
            try:
                return datetime.fromisoformat(raw)
            except ValueError:
                return None

        return None

    @property
    def last_event(self) -> Optional[AvatarEvent]:
        return self._last_event
