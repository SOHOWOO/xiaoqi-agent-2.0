from __future__ import annotations

from typing import Protocol, runtime_checkable

from .models import (
    LLMRequest,
    LLMResponse,
)


@runtime_checkable
class LLMProvider(Protocol):
    """
    小七统一大模型接口。
    """

    def chat(
        self,
        request: LLMRequest,
    ) -> LLMResponse:
        """
        发送聊天请求。
        """
        ...
