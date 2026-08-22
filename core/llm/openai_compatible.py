from __future__ import annotations

from ..chat.openai_compatible import (
    OpenAICompatibleProvider
)

from .models import (
    LLMRequest,
    LLMResponse,
)


class OpenAILLMProvider:

    def __init__(self):
        self.client = OpenAICompatibleProvider()

    def chat(
        self,
        request: LLMRequest,
    ) -> LLMResponse:

        prompt = "\n".join(
            [
                m.content
                for m in request.messages
            ]
        )

        result = self.client.generate(
            prompt
        )

        return LLMResponse(
            content=result
        )
