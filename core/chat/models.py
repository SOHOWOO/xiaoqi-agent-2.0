from __future__ import annotations

from dataclasses import dataclass

from ..memory import MemoryContext
from ..state import InteractionState, LifeState


@dataclass(frozen=True)
class ChatResult:
    """一次文本对话处理后的结构化结果。

    Chat Core 不负责生成最终回复。
    它只负责把：
    - 用户消息
    - 相关记忆
    - 当前生活状态
    - 当前互动状态

    整理成未来 LLM 可以直接消费的数据。
    """

    user_message: str
    memory_context: MemoryContext
    life_state: LifeState
    interaction_state: InteractionState

    proactive_interests: list = None
    proactive_messages: list = None

    def memory_text(self) -> str:
        """返回适合直接提供给 LLM 的记忆文本。"""

        return self.memory_context.as_text()
