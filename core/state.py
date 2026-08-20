from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import List, Optional

from .events import MemoryTier


@dataclass
class LifeState:
    current_time: Optional[datetime] = None
    current_slot_id: Optional[str] = None
    current_activity: Optional[str] = None
    fatigue: float = 0.5
    energy: float = 0.7


@dataclass
class InteractionState:
    last_user_interaction_at: Optional[datetime] = None

    def time_since_interaction(
        self,
        current_time: datetime,
    ) -> Optional[timedelta]:
        if self.last_user_interaction_at is None:
            return None

        delta = current_time - self.last_user_interaction_at

        if delta < timedelta(0):
            delta = timedelta(0)

        return delta


@dataclass(frozen=True)
class GroundTruthEntry:
    event_id: str
    event_type: str
    timestamp: datetime
    importance: int
    source: str
    tier: int = MemoryTier.TIER_1_GROUND_TRUTH


@dataclass
class GroundTruthStore:
    entries: List[GroundTruthEntry] = field(default_factory=list)

    def add(self, entry: GroundTruthEntry) -> None:
        self.entries.append(entry)


@dataclass
class SimulationResult:
    events: List[object] = field(default_factory=list)
    slots_seen: List[str] = field(default_factory=list)
    life_state: LifeState = field(default_factory=LifeState)
    interaction_state: InteractionState = field(
        default_factory=InteractionState
    )
