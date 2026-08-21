from __future__ import annotations

from datetime import datetime

from ..events import SimulationEvent
from ..memory.proactive import ProactiveInterest
from .proactive_engine import ProactiveEngine


class ProactiveScheduler:
    """主动关注调度器。"""

    def __init__(
        self,
        engine: ProactiveEngine | None = None,
    ):
        self.engine = (
            engine
            if engine is not None
            else ProactiveEngine()
        )


    def tick(
        self,
        interests: list[ProactiveInterest],
        now: datetime,
    ) -> list[SimulationEvent]:

        proactive_events = self.engine.evaluate(
            interests,
            now,
        )

        events = []

        for event in proactive_events:
            events.append(
                SimulationEvent(
                    event_id=(
                        f"proactive:"
                        f"{event.interest.interest_id}"
                    ),
                    event_type="proactive_interest",
                    slot_id=event.interest.interest_id,
                    start_time=now,
                    end_time=now,
                    importance=int(
                        event.interest.importance * 10
                    ),
                    source="proactive_engine",
                )
            )

        return events
