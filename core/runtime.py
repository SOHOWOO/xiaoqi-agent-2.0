from __future__ import annotations

from .life_loop import LifeLoop
from .memory import MemoryManager
from .relationship import RelationshipEngine


class AgentRuntime:
    """
    小七 Agent 运行时总控。

    统一管理：
    - LifeLoop
    - Memory
    - Relationship
    """

    def __init__(
        self,
        life_loop: LifeLoop,
    ):
        self.life_loop = life_loop

        self.memory_manager: MemoryManager = (
            life_loop.memory_manager
        )

        self.memory_store = (
            life_loop.memory_store
        )

        self.relationship_engine = (
            RelationshipEngine()
        )

    @property
    def current_time(self):
        return self.life_loop.current_time

    @property
    def life_state(self):
        return self.life_loop.life_state

    @property
    def interaction_state(self):
        return self.life_loop.interaction_state

    def get_proactive_events(self):
        return self.life_loop.get_proactive_events()

