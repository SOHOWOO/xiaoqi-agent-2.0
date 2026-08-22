from datetime import datetime, timedelta

import pytest

from core.relationship import (
    RelationshipEngine,
    RelationshipState,
)
from core.time_engine import DEFAULT_TZ


def _dt(day: int = 1, hour: int = 10) -> datetime:
    return datetime(2026, 8, day, hour, 0, tzinfo=DEFAULT_TZ)


def test_initial_stage_is_stranger():
    engine = RelationshipEngine()
    assert engine.state.stage == "陌生"


def test_interaction_grows_dimensions():
    engine = RelationshipEngine()
    baseline = RelationshipState()

    engine.update(
        "user_interaction",
        intensity=1.0,
        now=_dt(1),
    )

    state = engine.state
    assert state.familiarity > baseline.familiarity
    assert state.attachment > baseline.attachment
    assert state.trust > baseline.trust
    assert state.interaction_count == 1
    assert state.last_interaction_at == _dt(1)


def test_different_events_have_different_effects():
    help_engine = RelationshipEngine()
    help_engine.update(
        "mutual_help",
        intensity=1.0,
        now=_dt(1),
    )

    talk_engine = RelationshipEngine()
    talk_engine.update(
        "user_interaction",
        intensity=1.0,
        now=_dt(1),
    )

    assert (
        help_engine.state.trust > talk_engine.state.trust
    )


def test_conflict_erodes_trust():
    engine = RelationshipEngine()
    engine.update("user_interaction", intensity=1.0, now=_dt(1))
    peak_trust = engine.state.trust

    engine.update("conflict", intensity=1.0, now=_dt(1))

    assert engine.state.trust < peak_trust


def test_tick_decays_over_absence():
    engine = RelationshipEngine()

    engine.tick(_dt(1))
    engine.update("user_interaction", intensity=1.0, now=_dt(1))

    peak_attachment = engine.state.attachment

    engine.tick(_dt(8))

    assert engine.state.attachment < peak_attachment


def test_tick_no_decay_when_recent():
    engine = RelationshipEngine()
    moment = _dt(1)
    engine.update("user_interaction", intensity=1.0, now=moment)
    peak = engine.state.attachment

    engine.tick(moment)

    assert engine.state.attachment == pytest.approx(
        peak,
        abs=1e-9,
    )


def test_continuous_tick_matches_total_decay():
    """连续 672 次 15min tick 的衰减 == 一次 7 天的衰减。"""

    import math

    engine = RelationshipEngine()
    start = _dt(1)

    engine.tick(start)
    engine.update("user_interaction", intensity=1.0, now=start)

    peak = engine.state.attachment

    for i in range(1, 672 + 1):
        engine.tick(start + timedelta(minutes=15 * i))

    expected = peak * math.exp(-0.008 * 7)

    assert engine.state.attachment == pytest.approx(
        expected,
        abs=1e-6,
    )


def test_first_tick_does_not_set_last_interaction():
    """引擎 tick 不应把"从未互动"误标为已互动。"""

    engine = RelationshipEngine()
    engine.tick(_dt(1))

    assert engine.state.last_interaction_at is None


def test_intimacy_and_stage_derived():
    state = RelationshipState(
        trust=0.5,
        attachment=0.9,
        familiarity=0.9,
        shared_experience=0.9,
    )

    assert state.intimacy > 0.85
    assert state.stage == "亲密"


def test_round_trip_serialization():
    engine = RelationshipEngine()
    engine.update("user_interaction", intensity=1.0, now=_dt(1))
    engine.update("mutual_help", intensity=1.0, now=_dt(2))

    data = engine.to_dict()

    restored = RelationshipEngine()
    restored.restore(data)

    assert restored.state.trust == pytest.approx(
        engine.state.trust, abs=1e-9
    )
    assert restored.state.attachment == pytest.approx(
        engine.state.attachment, abs=1e-9
    )
    assert restored.state.familiarity == pytest.approx(
        engine.state.familiarity, abs=1e-9
    )
    assert restored.state.shared_experience == pytest.approx(
        engine.state.shared_experience, abs=1e-9
    )
    assert (
        restored.state.interaction_count
        == engine.state.interaction_count
    )
    assert (
        restored.state.last_interaction_at
        == engine.state.last_interaction_at
    )


def test_build_context_contains_dimensions():
    engine = RelationshipEngine()
    engine.update("user_interaction", intensity=1.0, now=_dt(1))

    text = engine.build_context()

    assert "信任度" in text
    assert "依恋度" in text
    assert "熟悉度" in text
    assert "共同经历" in text


def test_interact_backwards_compatible():
    engine = RelationshipEngine()
    engine.interact(now=_dt(1))

    assert engine.state.interaction_count == 1
    assert engine.state.last_interaction_at == _dt(1)


def test_invalid_intensity_rejected():
    engine = RelationshipEngine()

    with pytest.raises(ValueError):
        engine.update(
            "user_interaction",
            intensity=1.5,
            now=_dt(1),
        )
