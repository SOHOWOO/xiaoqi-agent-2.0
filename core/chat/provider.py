from __future__ import annotations

from typing import Protocol, runtime_checkable

from .request import ChatRequest


@runtime_checkable
class ResponseProvider(Protocol):
    """统一的文本生成模型接口。"""

    def generate(self, request: ChatRequest) -> str:
        """根据 ChatRequest 生成文本回复。"""
        ...


class StubResponseProvider:
    """用于测试 Chat Core 的本地假模型。"""

    def generate(self, request: ChatRequest) -> str:
        """返回确定性的本地测试回复。"""

        if not request.messages:
            raise ValueError("messages cannot be empty")

        return "小七收到了你的消息。"
