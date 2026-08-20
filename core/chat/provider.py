from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class ResponseProvider(Protocol):
    """统一的文本生成模型接口。"""

    def generate(self, prompt: str) -> str:
        """根据 Prompt 生成文本回复。"""
        ...


class StubResponseProvider:
    """用于测试 Chat Core 的本地假模型。"""

    def generate(self, prompt: str) -> str:
        """返回确定性的本地测试回复。"""

        if not prompt.strip():
            raise ValueError("prompt cannot be empty")

        return "小七收到了你的消息。"
