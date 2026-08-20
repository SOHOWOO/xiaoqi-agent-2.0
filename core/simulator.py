from __future__ import annotations

from datetime import datetime
from typing import List, Set

from .energy_engine import update_energy
from .events import MemoryTier, MicroEventEngine, SimulationEvent
from .schedule_engine import NEEDS_REVIEW, ScheduleEngine
from .state import GroundTruthStore, InteractionState, LifeState, SimulationResult
from .time_engine import DEFAULT_TZ, ensure_aware, iter_days


class LifeSimulator:
    """Minimal deterministic Life Simulation Core.

    - 微事件按 SlotOccurrence 判定一次。
    - 判定结果由稳定 hash 决定，与 simulate() 被分成几段无关。
    - 已发出事件由 _emitted_event_keys 去重。
    - 模拟时钟 monotonic：禁止时间倒退。
    - fatigue / energy 根据 Slot 实际经过时间持续更新。
    - SimulationResult 返回独立状态快照。
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

        # Simulation Clock：禁止时间倒退
        if (
            self.life_state.current_time is not None
            and from_time < self.life_state.current_time
        ):
            raise ValueError(
                "simulation time cannot move backwards: "
                f"current={self.life_state.current_time.isoformat()}, "
                f"from={from_time.isoformat()}"
            )

        # 空区间或反向区间：
        # 不推进模拟时钟，只返回当前状态快照。
        if to_time <= from_time:
            return SimulationResult(
                events=[],
                slots_seen=[],
                life_state=self._snapshot_life_state(),
                interaction_state=self._snapshot_interaction_state(),
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
                # 只处理当前 simulate 区间
                # 与这个 Slot occurrence 的实际交集。
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

                slots_seen.append(
                    occ.slot.slot_id
                )

                # -------------------------------------------------
                # Energy / Fatigue Engine
                # -------------------------------------------------
                #
                # 根据这个 Slot 在当前模拟区间内实际经过的时间，
                # 更新 fatigue 和 energy。
                #
                # 例如：
                #
                # morning_clinic 09:00 - 12:00
                #
                # 如果本次只模拟：
                # 09:30 - 10:00
                #
                # 那么这里只计算 0.5 小时，
                # 而不是把整个 Slot 算进去。
                #
                hours = (
                    overlap_end - overlap_start
                ).total_seconds() / 3600.0

                update_energy(
                    self.life_state,
                    occ.slot,
                    hours,
                )

                # -------------------------------------------------
                # Micro Events
                # -------------------------------------------------

                for rule in occ.slot.events:
                    occurred = self.micro_events.evaluate(
                        occ.occurrence_id,
                        rule.event_type,
                        rule.probability,
                    )

                    if not occurred:
                        continue

                    event_key = (
                        f"{occ.occurrence_id}:"
                        f"{rule.event_type}"
                    )

                    # 防止连续 simulate 时重复发出
                    # 同一个 Slot occurrence 的事件。
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

                    self._emitted_event_keys.add(
                        event_key
                    )

        # ---------------------------------------------------------
        # Simulation Clock
        # ---------------------------------------------------------
        #
        # 只有整个 simulate 成功完成后，
        # 才推进内部模拟时间。
        #
        self.life_state.current_time = to_time
        self.life_state.current_slot_id = current_slot_id
        self.life_state.current_activity = current_activity

        # ---------------------------------------------------------
        # 返回独立快照
        # ---------------------------------------------------------
        #
        # 不直接返回 self.life_state，
        # 防止下一次 simulate 修改当前状态后，
        # 上一次 SimulationResult 也跟着变化。
        #
        return SimulationResult(
            events=events,
            slots_seen=slots_seen,
            life_state=self._snapshot_life_state(),
            interaction_state=self._snapshot_interaction_state(),
        )

    def _snapshot_life_state(self) -> LifeState:
        """返回当前 LifeState 的独立副本。"""

        return LifeState(
            current_time=self.life_state.current_time,
            current_slot_id=self.life_state.current_slot_id,
            current_activity=self.life_state.current_activity,
            fatigue=self.life_state.fatigue,
            energy=self.life_state.energy,
        )

    def _snapshot_interaction_state(
        self,
    ) -> InteractionState:
        """返回当前 InteractionState 的独立副本。"""

        return InteractionState(
            last_user_interaction_at=(
                self.interaction_state.last_user_interaction_at
            ),
        )