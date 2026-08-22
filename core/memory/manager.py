from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from .models import MemoryRecord, MemoryType
from .policy import can_modify, is_long_term_candidate
from .store import MemoryStore
from .memory_router import MemoryRouter
from .layers import MemoryLayers
from .memory_stores import (
    DiaryMemoryStore,
    EpisodicMemoryStore,
    RelationshipMemoryStore,
    SemanticMemoryStore,
)


class MemoryAction:
    ADD = "add"
    UPDATE = "update"
    IGNORE = "ignore"
    REJECT = "reject"


@dataclass(frozen=True)
class MemoryDecision:
    action: str
    reason: str
    target_memory_id: Optional[str] = None
    route: Optional[str] = None


class MemoryManager:
    """Memory Core unified entry point for Memory 2.0."""

    def __init__(self, store: MemoryStore):
        self.store = store
        self.router = MemoryRouter()
        self.layers = MemoryLayers()

        self.episodic_store = EpisodicMemoryStore()
        self.relationship_store = RelationshipMemoryStore()
        self.semantic_store = SemanticMemoryStore()
        self.diary_store = DiaryMemoryStore()

        from .proactive import ProactiveInterestManager
        self.proactive_manager = ProactiveInterestManager()

    def _write_layer_store(self, route: str, content: str):
        if route == "episodic":
            self.episodic_store.add(content)
        elif route == "relationship":
            self.relationship_store.add(content)
        elif route == "semantic":
            self.semantic_store.add(content)
        else:
            self.diary_store.add(content)

    def decide(self, memory: MemoryRecord, target_memory: Optional[MemoryRecord] = None) -> MemoryDecision:
        route = self.router.route(
            str(getattr(memory, "content", "")),
            int(getattr(memory, "importance", 0)),
        )

        if target_memory is None:
            if memory.memory_type == MemoryType.CANONICAL:
                return MemoryDecision(MemoryAction.ADD, "canonical new memory", route=route.channel)
            if is_long_term_candidate(memory.memory_type, memory.importance):
                return MemoryDecision(MemoryAction.ADD, "qualified long term memory", route=route.channel)
            return MemoryDecision(MemoryAction.IGNORE, "not qualified for long term storage", route=route.channel)

        if memory.memory_type == MemoryType.CANONICAL and target_memory.memory_type == MemoryType.CANONICAL:
            return MemoryDecision(MemoryAction.UPDATE, "canonical update", target_memory.memory_id, route.channel)

        if not can_modify(memory.memory_type, target_memory.memory_type):
            return MemoryDecision(MemoryAction.REJECT, "modification blocked by policy", target_memory.memory_id, route.channel)

        if is_long_term_candidate(memory.memory_type, memory.importance):
            return MemoryDecision(MemoryAction.UPDATE, "qualified update", target_memory.memory_id, route.channel)

        return MemoryDecision(MemoryAction.IGNORE, "update not important enough", target_memory.memory_id, route.channel)

    def add_if_allowed(self, memory: MemoryRecord) -> MemoryDecision:
        decision = self.decide(memory)
        if decision.action == MemoryAction.ADD:
            self.store.add(memory)
            route = decision.route or "diary"
            self.layers.add(route, str(getattr(memory, "content", "")))
            self._write_layer_store(route, str(getattr(memory, "content", "")))
            self.proactive_manager.register(memory)
        return decision

    def update_if_allowed(self, memory: MemoryRecord, target_memory: MemoryRecord) -> MemoryDecision:
        decision = self.decide(memory, target_memory)
        if decision.action == MemoryAction.UPDATE:
            assert decision.target_memory_id is not None
            self.store.update(decision.target_memory_id, memory)
        return decision

    def get_proactive_interests(self):
        return self.proactive_manager.all()

    def get_memory_layers(self):
        return self.layers.snapshot()

    def process(self, memory: MemoryRecord, target_memory: Optional[MemoryRecord] = None) -> MemoryDecision:
        if target_memory is None:
            return self.add_if_allowed(memory)
        return self.update_if_allowed(memory, target_memory)
