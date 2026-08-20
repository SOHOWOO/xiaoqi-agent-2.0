from __future__ import annotations

from dataclasses import dataclass

from .state import LifeState
from .schedule_engine import LifeSlot


@dataclass(frozen=True)
class Presence:
    slot_id: str
    activity: str
    fatigue: float
    energy: float

    def describe(self) -> str:
        return (
            f"小七现在正在「{self.activity}」，"
            f"疲劳度 {self.fatigue:.2f}，"
            f"精力 {self.energy:.2f}。"
        )


def build_presence(slot: LifeSlot, life_state: LifeState) -> Presence:
    return Presence(
        slot_id=slot.slot_id,
        activity=slot.name,
        fatigue=life_state.fatigue,
        energy=life_state.energy,
    )
