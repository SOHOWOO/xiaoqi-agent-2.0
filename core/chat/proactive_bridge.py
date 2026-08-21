from __future__ import annotations

from ..memory.models import MemoryRecord, MemoryType
from ..memory.models import MemorySource


class ProactiveBridge:
    """连接聊天分析和主动关注系统。"""

    def register_from_text(
        self,
        text: str,
        life_loop,
    ):
        if not text.strip():
            return None

        memory = MemoryRecord(
            memory_id=(
                f"chat_interest:"
                f"{len(life_loop.memory_store.all())+1}"
            ),
            memory_type=MemoryType.INTERACTION,
            content=text,
            created_at=life_loop.current_time,
            source=MemorySource.CONVERSATION,
            importance=0.85,
            confidence=1.0,
        )

        return (
            life_loop.memory_manager
            .proactive_manager
            .register(memory)
        )
