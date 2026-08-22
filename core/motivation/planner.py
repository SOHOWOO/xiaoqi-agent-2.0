from __future__ import annotations

from typing import Any, List

from .models import Motivation, MotivationType

_ACTION_BY_MOTIVATION = {
    MotivationType.CRAVING_CONTACT: "chat",
    MotivationType.COMFORT: "comfort",
    MotivationType.SHARE: "share",
    MotivationType.REMIND: "remind",
    MotivationType.PLAY: "play",
}


class ActionPlanner:
    """行为规划器。

    把高阶动机映射为可执行的候选信号（ProactiveSignal），
    交由 Proactive 门控与决策。
    """

    def plan(
        self,
        motivations: List[Motivation],
        ctx: Any,
    ) -> list:
        from ..proactive.models import ProactiveSignal

        signals: list = []

        for motivation in motivations:
            signals.append(
                ProactiveSignal(
                    signal_type=(
                        f"motivation:"
                        f"{motivation.type.value}"
                    ),
                    reason="；".join(
                        motivation.reasons
                    ),
                    score=motivation.intensity,
                    suggested_action=(
                        _ACTION_BY_MOTIVATION[
                            motivation.type
                        ]
                    ),
                    payload=motivation.payload,
                )
            )

        return signals
