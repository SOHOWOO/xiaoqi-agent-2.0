from __future__ import annotations

from dataclasses import dataclass
from typing import List


@dataclass
class ChatMessage:
    role: str
    content: str


@dataclass
class ChatRequest:
    """
    Agent 内部统一请求协议。

    后续用于连接：
    - OpenAI compatible API
    - DeepSeek
    - Ollama
    - 本地模型
    """

    messages: List[ChatMessage]

    system_prompt: str | None = None

    metadata: dict | None = None

    def to_text(self) -> str:
        """
        兼容旧 Prompt 字符串模式。
        """

        parts: list[str] = []

        if self.system_prompt:
            parts.append(
                self.system_prompt
            )

        for message in self.messages:
            parts.append(
                message.content
            )

        return "\n\n".join(parts)

    def __contains__(self, item: str) -> bool:
        """
        兼容旧测试：
        "xxx" in ChatRequest
        """

        return item in self.to_text()

    def __str__(self) -> str:
        return self.to_text()
