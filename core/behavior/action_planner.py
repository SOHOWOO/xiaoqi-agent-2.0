from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Any


@dataclass
class PlannedAction:
    action: str
    reason: str
    priority: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


class ActionPlanner:
    """
    Converts internal desires and state into possible actions.

    This layer intentionally does not execute actions. It only decides
    what Xiaoqi wants to do. Execution will be handled by bridges
    (chat, avatar, voice, etc.).
    """

    def plan(self, desire_state: Dict[str, float], context: Dict[str, Any] | None = None) -> PlannedAction:
        context = context or {}

        loneliness = desire_state.get("loneliness", 0)
        attachment = desire_state.get("attachment", 0)
        curiosity = desire_state.get("curiosity", 0)

        if loneliness > 70 and attachment > 60:
            return PlannedAction(
                action="start_conversation",
                reason="high loneliness and strong attachment",
                priority=min(1.0, (loneliness + attachment) / 200),
            )

        if curiosity > 75:
            return PlannedAction(
                action="ask_question",
                reason="curiosity drive is high",
                priority=curiosity / 100,
            )

        return PlannedAction(
            action="wait",
            reason="no strong internal desire detected",
            priority=0.0,
        )
