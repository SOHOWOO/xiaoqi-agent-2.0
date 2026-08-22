from __future__ import annotations

from dataclasses import dataclass


@dataclass
class DesireState:
    """Internal drives that can trigger future proactive actions."""

    loneliness: float = 0.0
    curiosity: float = 0.0
    attachment: float = 0.0
    need_to_interact: float = 0.0


class DesireSystem:
    """Convert internal state into actionable desire signals.

    This is intentionally independent from chat/avatar layers.
    It will later consume emotion, neurochemical and relationship models.
    """

    def __init__(self):
        self.state = DesireState()

    def update(self, *, loneliness=0.0, curiosity=0.0, attachment=0.0):
        self.state.loneliness = float(loneliness)
        self.state.curiosity = float(curiosity)
        self.state.attachment = float(attachment)

        self.state.need_to_interact = (
            self.state.loneliness * 0.5
            + self.state.attachment * 0.3
            + self.state.curiosity * 0.2
        )

        return self.state

    def should_act(self, threshold: float = 60.0) -> bool:
        return self.state.need_to_interact >= threshold
