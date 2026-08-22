from __future__ import annotations

from dataclasses import dataclass
from typing import List


@dataclass(frozen=True)
class LLMMessage:
    """
    标准聊天消息。
    """

    role: str
    content: str


@dataclass(frozen=True)
class LLMRequest:
    """
    发送给模型的请求。
    """

    messages: List[LLMMessage]

    model: str | None = None

    temperature: float = 0.7


@dataclass(frozen=True)
class LLMResponse:
    """
    模型返回结果。
    """

    content: str

    model: str | None = None

    usage: dict | None = None
