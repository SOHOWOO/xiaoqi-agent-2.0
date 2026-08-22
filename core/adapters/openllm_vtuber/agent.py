from __future__ import annotations

from typing import AsyncIterator, Optional

from .emotion_map import map_emotion_to_expression
from .types import (
    Actions,
    BatchInput,
    DisplayText,
    SentenceOutput,
    TextSource,
)


class XiaoqiAgent:
    """xiaoqi-agent 的 Open-LLM-VTuber Agent 适配层（协议对齐）。

    实现 OLV 的 AgentInterface：
        async chat(BatchInput) -> AsyncIterator[SentenceOutput]
        handle_interrupt(heard_response)
        set_memory_from_history(conf_uid, history_uid)

    不依赖 OLV 包，类型签名与 OLV 完全兼容，
    真实接入时可直接挂载到 OLV 的 AgentFactory。
    """

    NAME = "小七"

    def __init__(
        self,
        life_loop,
        chat_service,
        *,
        name: str = NAME,
    ) -> None:
        self.life_loop = life_loop
        self.chat_service = chat_service
        self.name = name

        self._interrupted = False
        self.interrupts: list[dict] = []
        self._history_ref: Optional[tuple] = None

    # ---------------------------------------------------------
    # AgentInterface
    # ---------------------------------------------------------

    async def chat(
        self,
        input_data: BatchInput,
    ) -> AsyncIterator[SentenceOutput]:
        """处理一次输入，流式产出文本输出。"""

        if self._is_proactive_speak(input_data):
            for output in self._handle_proactive():
                yield output
            return

        text = self._extract_input_text(input_data)

        if not text:
            return

        result = self.chat_service.handle_message(text)
        response = self.chat_service.respond(result)

        yield self._build_output(response)

    def handle_interrupt(
        self,
        heard_response: str,
    ) -> None:
        """用户打断：记录并清空待发送的主动消息。"""

        self._interrupted = True

        self.interrupts.append(
            {
                "heard": heard_response,
                "at": (
                    self.life_loop.current_time
                    if self.life_loop.current_time
                    else None
                ),
            }
        )

        # 打断后不再强行推送主动消息
        self.life_loop.get_pending_proactive_messages()

    def set_memory_from_history(
        self,
        conf_uid: str,
        history_uid: str,
    ) -> None:
        """记录 OLV 历史引用（桩，后续可加载到工作记忆）。"""

        self._history_ref = (conf_uid, history_uid)

    # ---------------------------------------------------------
    # 内部实现
    # ---------------------------------------------------------

    def _is_proactive_speak(
        self,
        input_data: BatchInput,
    ) -> bool:
        metadata = input_data.metadata or {}
        return bool(metadata.get("proactive_speak"))

    def _extract_input_text(
        self,
        input_data: BatchInput,
    ) -> Optional[str]:
        for text in input_data.texts:
            if text.source != TextSource.INPUT:
                continue

            content = text.content.strip() if text.content else ""

            if content:
                return content

        return None

    def _handle_proactive(self):
        """处理主动说话输入：发送 pending 主动消息。"""

        messages = (
            self.life_loop.get_pending_proactive_messages()
        )

        for message in messages:
            yield self._build_output(message.content)

    def _current_expression(self) -> str:
        emotion = self.life_loop.emotion.state()

        return map_emotion_to_expression(
            emotion.dominant().value
        )

    def _build_output(
        self,
        text: str,
    ) -> SentenceOutput:
        return SentenceOutput(
            display_text=DisplayText(
                text=text,
                name=self.name,
            ),
            tts_text=text,
            actions=Actions(
                expressions=[self._current_expression()]
            ),
        )
