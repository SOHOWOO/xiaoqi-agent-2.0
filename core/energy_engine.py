from __future__ import annotations

from dataclasses import dataclass

from .schedule_engine import LifeSlot
from .state import LifeState


@dataclass(frozen=True)
class EnergyProfile:
    fatigue_delta_per_hour: float
    energy_delta_per_hour: float


DEFAULT_PROFILES = {
    "sleep": EnergyProfile(-0.20, 0.20),
    "morning_prep": EnergyProfile(0.02, -0.02),
    "commute": EnergyProfile(0.05, -0.05),
    "morning_clinic": EnergyProfile(0.12, -0.12),
    "lunch_break": EnergyProfile(-0.10, 0.10),
    "afternoon_clinic": EnergyProfile(0.15, -0.15),
    "commute_grocery": EnergyProfile(0.08, -0.08),
    "cooking_dinner": EnergyProfile(0.06, -0.06),
    "home_leisure": EnergyProfile(-0.05, 0.05),
    "pre_sleep": EnergyProfile(-0.03, 0.03),
}


def update_energy(
    life_state: LifeState,
    slot: LifeSlot,
    hours: float,
) -> LifeState:
    profile = DEFAULT_PROFILES.get(
        slot.slot_id,
        EnergyProfile(0.0, 0.0),
    )

    life_state.fatigue = min(
        1.0,
        max(0.0, life_state.fatigue + profile.fatigue_delta_per_hour * hours),
    )

    life_state.energy = min(
        1.0,
        max(0.0, life_state.energy + profile.energy_delta_per_hour * hours),
    )

    return life_state
