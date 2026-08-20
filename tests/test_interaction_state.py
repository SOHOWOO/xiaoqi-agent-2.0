from datetime import timedelta

from core.simulator import LifeSimulator
from core.state import InteractionState
from core.time_engine import make_aware


def test_last_user_interaction_is_independent():
    last = make_aware(2026, 8, 20, 10, 0)
    interaction = InteractionState(last_user_interaction_at=last)

    sim = LifeSimulator(
        seed=1,
        interaction_state=interaction,
    )

    from_time = make_aware(2026, 8, 20, 9, 0)
    to_time = make_aware(2026, 8, 20, 18, 0)

    result = sim.simulate(from_time, to_time)

    assert result.interaction_state.last_user_interaction_at == last

    assert (
        result.interaction_state.time_since_interaction(to_time)
        == timedelta(hours=8)
    )

    # Simulation time 不是 relationship interaction time
    assert result.life_state.current_time == to_time
    assert (
        result.life_state.current_time
        != result.interaction_state.last_user_interaction_at
    )
