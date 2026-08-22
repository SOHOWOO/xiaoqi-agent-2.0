from __future__ import annotations

from dataclasses import dataclass
from typing import List


@dataclass
class ChatMessage:
    role: str
    content: str


@dataclass
class ChatRequest:
    messages: List[ChatMessage]

    system_prompt: str | None = None

    metadata: dict | None = None
