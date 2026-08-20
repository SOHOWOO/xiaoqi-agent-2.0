from __future__ import annotations

from datetime import datetime
from typing import List, Set

from .events import MemoryTier, MicroEventEngine, SimulationEvent
from .schedule_engine import NEEDS_REVIEW, ScheduleEngine
from .state import GroundTruthStore, InteractionState, LifeState, SimulationResult
from .time_engine import DEFAULT_TZ, ensure_aware, iter_days


class LifeSimulator:
    """Minimal deterministic Life Simulation Core.

    - 微事件按 SlotOccurrence 判定一次。
    - 判定结果由稳定 hash 决定，与 simulate() 被分成几段无关。
    - 已发出事件由 _emitted_event_keys 去重。
    """

    def __init__(
        self,
        seed: int | None = None,
        schedule_config=None,
        interaction_state: InteractionState | None = None,
        tz=DEFAULT_TZ,
    ):
        self.tz = tz
        self.seed = seed
        self.schedule_engine = ScheduleEngine(schedule_config)
        self.micro_events = MicroEventEngine(seed=seed)
        self.life_state = LifeState()
        self.interaction_state = interaction_state or InteractionState()
        self.ground_truth = GroundTruthStore()
        self._emitted_event_keys: Set[str] = set()

    def simulate(
        self,
        from_time: datetime,
        to_time: datetime,
    ) -> SimulationResult:
        from_time = ensure_aware(from_time, self.tz)
        to_time = ensure_aware(to_time, self.tz)

        if to_time <= from_time:
            return SimulationResult(
                life_state=self.life_state,
                interaction_state=self.interaction_state,
            )

        events: List[SimulationEvent] = []
        slots_seen: List[str] = []

        current_slot_id = "NO_SLOT"
        current_activity = "NO_SLOT"

        for day, _day_start, _day_end in iter_days(
            from_time,
            to_time,
        ):
            occurrences = self.schedule_engine.slots_for_date(day)

            if occurrences == NEEDS_REVIEW:
                current_slot_id = NEEDS_REVIEW
                current_activity = NEEDS_REVIEW
                continue

            for occ in occurrences:
                overlap_start = max(
                    occ.start,
                    from_time,
                )
                overlap_end = min(
                    occ.end,
                    to_time,
                )

                if overlap_start >= overlap_end:
                    continue

                current_slot_id = occ.slot.slot_id
                current_activity = occ.slot.name
                slots_seen.append(occ.slot.slot_id)

                for rule in occ.slot.events:
                    occurred = self.micro_events.evaluate(
                        occ.occurrence_id,
                        rule.event_type,
                        rule.probability,
                    )

                    if not occurred:
                        continue

                    event_key = (
                        f"{occ.occurrence_id}:{rule.event_type}"
                    )

                    if event_key in self._emitted_event_keys:
                        continue

                    events.append(
                        SimulationEvent(
                            event_id=event_key,
                            event_type=rule.event_type,
                            slot_id=occ.slot.slot_id,
                            start_time=occ.start,
                            end_time=occ.end,
                            importance=rule.importance,
                            source=rule.source,
                            tier=MemoryTier.TIER_3_SIMULATED_LIFE,
                        )
                    )

                    self._emitted_event_keys.add(event_key)

        self.life_state.current_time = to_time
        self.life_state.current_slot_id = current_slot_id
        self.life_state.current_activity = current_activity

        return SimulationResult(
            events=events,
            slots_seen=slots_seen,
            life_state=self.life_state,
            interaction_state=self.interaction_state,
        )
