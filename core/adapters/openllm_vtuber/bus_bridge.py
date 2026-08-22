from __future__ import annotations

from .emotion_map import map_emotion_to_expression


class XiaoqiBusBridge:
    """xiaoqi-bus -> Open-LLM-VTuber 事件对接。

    把 xiaoqi 核心事件转换为 OLV 前端可消费的形式：
    - emotion_change  -> Actions.expressions（表情）
    - proactive_triggered -> proactive_speak（主动说话内容）

    真实接入时，订阅者把输出推送给 OLV 前端。
    """

    def __init__(
        self,
        event_bus,
        *,
        subscribe: bool = True,
    ) -> None:
        self.event_bus = event_bus

        self.last_expression: str | None = None
        self.last_emotion: str | None = None
        self.last_proactive: str | None = None

        if subscribe:
            event_bus.subscribe(
                "emotion_change",
                self._on_emotion_change,
            )
            event_bus.subscribe(
                "proactive_triggered",
                self._on_proactive,
            )

    def _on_emotion_change(
        self,
        data: dict | None,
    ) -> None:
        if not data:
            return

        to = data.get("to", "calm")

        self.last_emotion = to
        self.last_expression = map_emotion_to_expression(
            to
        )

    def _on_proactive(
        self,
        data: dict | None,
    ) -> None:
        if not data:
            return

        self.last_proactive = data.get("content")

    def expression_payload(self) -> dict | None:
        """OLV Actions.expressions 负载。"""

        if self.last_expression is None:
            return None

        return {
            "expressions": [self.last_expression]
        }

    def proactive_payload(self) -> dict | None:
        """OLV proactive_speak 输入负载。"""

        if self.last_proactive is None:
            return None

        return {
            "proactive_speak": True,
            "content": self.last_proactive,
        }
