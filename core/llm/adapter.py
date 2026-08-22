from __future__ import annotations

from ..chat.request import ChatRequest
from .models import (
    LLMRequest,
    LLMMessage,
    LLMResponse,
)


class ChatRequestAdapter:
    """
    Chat 层到 LLM 层转换器。
    """

    @staticmethod
    def convert(
        request: ChatRequest,
    ) -> LLMRequest:

        return LLMRequest(
            messages=[
                LLMMessage(
                    role=m.role,
                    content=m.content,
                )
                for m in request.messages
            ]
        )


class LLMChatAdapter:
    """
    将 LLMProvider 包装成 Chat Provider。
    """

    def __init__(self, provider):
        self.provider = provider

    def generate(self, request):
        llm_request = ChatRequestAdapter.convert(
            request
        )

        response: LLMResponse = self.provider.chat(
            llm_request
        )

        return response.content
