from __future__ import annotations

from dataclasses import dataclass


@dataclass
class NeurochemicalState:
    """Behavior-oriented internal chemistry model.

    Values are simulation parameters, not medical measurements.
    """

    dopamine: float = 50.0
    fatigue: float = 20.0
    cortisol: float = 10.0
    attachment: float = 50.0
    curiosity: float = 50.0

    def clamp(self) -> None:
        for field in self.__dataclass_fields__:
            value = getattr(self, field)
            setattr(self, field, max(0.0, min(100.0, value)))


class NeurochemicalEngine:
    def __init__(self, state: NeurochemicalState | None = None):
        self.state = state or NeurochemicalState()

    def reward(self, amount: float = 5.0) -> None:
        self.state.dopamine += amount
        self.state.clamp()

    def stress(self, amount: float = 5.0) -> None:
        self.state.cortisol += amount
        self.state.clamp()

    def rest(self, amount: float = 5.0) -> None:
        self.state.fatigue -= amount
        self.state.clamp()
