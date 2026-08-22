from __future__ import annotations

from .models import (
    LLMRequest,
    LLMResponse,
)


class StubLLMProvider:
    """
    本地测试模型。
    """

    def chat(
        self,
        request: LLMRequest,
    ) -> LLMResponse:

        if not request.messages:
            raise ValueError(
                "messages cannot be empty"
            )

        return LLMResponse(
            content="小七收到了你的消息。",
            model="stub",
        )
