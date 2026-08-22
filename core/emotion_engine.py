from __future__ import annotations

from dataclasses import dataclass


@dataclass
class EmotionState:
    happiness: float = 50.0
    loneliness: float = 20.0
    stress: float = 10.0
    affection: float = 50.0
    curiosity: float = 50.0

    def clamp(self) -> None:
        for field in self.__dataclass_fields__:
            setattr(self, field, max(0.0, min(100.0, getattr(self, field))))


class EmotionEngine:
    def __init__(self, state: EmotionState | None = None):
        self.state = state or EmotionState()

    def apply_interaction(self, positive: bool = True) -> EmotionState:
        if positive:
            self.state.happiness += 3
            self.state.loneliness -= 3
            self.state.affection += 1
        else:
            self.state.stress += 3
        self.state.clamp()
        return self.state
