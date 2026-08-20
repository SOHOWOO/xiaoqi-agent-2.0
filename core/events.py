from __future__ import annotations

import hashlib
import random
from dataclasses import dataclass
from datetime import datetime
from enum import IntEnum


class MemoryTier(IntEnum):
    TIER_1_GROUND_TRUTH = 1
    TIER_2_RELATIONSHIP_MEMORY = 2
    TIER_3_SIMULATED_LIFE = 3
    TIER_4_FANTASY_DREAM = 4


@dataclass(frozen=True)
class SimulationEvent:
    event_id: str
    event_type: str
    slot_id: str
    start_time: datetime
    end_time: datetime
    importance: int
    source: str
    tier: int = MemoryTier.TIER_3_SIMULATED_LIFE


@dataclass(frozen=True)
class GroundTruthEvent:
    event_id: str
    event_type: str
    timestamp: datetime
    importance: int
    source: str
    tier: int = MemoryTier.TIER_1_GROUND_TRUTH


class MicroEventEngine:
    """Deterministic per-occurrence event decider."""

    def __init__(self, seed: int | None = None):
        self.seed = seed
        self._decision_cache: dict[tuple[str, str], bool] = {}

    def evaluate(
        self,
        occurrence_id: str,
        event_type: str,
        probability: float,
    ) -> bool:
        key = (occurrence_id, event_type)

        if key not in self._decision_cache:
            self._decision_cache[key] = self._roll(
                occurrence_id,
                event_type,
                probability,
            )

        return self._decision_cache[key]

    def _roll(
        self,
        occurrence_id: str,
        event_type: str,
        probability: float,
    ) -> bool:
        if probability <= 0.0:
            return False

        if probability >= 1.0:
            return True

        seed_str = f"{self.seed}:{occurrence_id}:{event_type}"

        digest = hashlib.sha256(
            seed_str.encode("utf-8")
        ).digest()

        rng = random.Random(
            int.from_bytes(digest[:8], "big")
        )

        return rng.random() < probability
