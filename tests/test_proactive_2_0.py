from datetime import date, datetime, timedelta

import pytest

from core.emotion import (
    EmotionEngine,
    EmotionEvent,
    EmotionType,
)
from core.neurochemical import (
    NeurochemicalEngine,
    NeurochemicalStimulus,
    StimulusType,
)
from core.proactive import (
    EmotionSignalGenerator,
    MemorySignalGenerator,
    NeurochemicalSignalGenerator,
    ProactiveContext,
    ProactiveGate,
    ProactiveSignal,
    TimeSignalGenerator,
    UnifiedProactiveEngine,
)
from core.time_engine import DEFAULT_TZ


def _dt(hour: int, minute: int = 0, day: int = 22) -> datetime:
    return datetime(2026, 8, day, hour, minute, tzinfo=DEFAULT_TZ)


class _FakeLifeState:
    energy = 0.7


class _FakeRelationship:
    class _State:
        intimacy = 0.8
        familiarity = 0.9
        stage = "亲密"

    state = _State()


# ---------------------------------------------------------
# 信号生成器
# ---------------------------------------------------------


def test_emotion_signal_lonely():
    emotion = EmotionEngine()
    emotion.apply_event(EmotionEvent(EmotionType.LONELY, 1.0))

    ctx = ProactiveContext(
        now=_dt(20),
        emotion_state=emotion.state(),
    )

    signals = EmotionSignalGenerator().generate(ctx)

    assert any(
        s.signal_type == "emotion:lonely"
        and s.suggested_action == "chat"
        for s in signals
    )


def test_emotion_signal_none_when_calm():
    emotion = EmotionEngine()
    ctx = ProactiveContext(
        now=_dt(20),
        emotion_state=emotion.state(),
    )

    assert EmotionSignalGenerator().generate(ctx) == []


def test_neurochemical_signal_requires_absence():
    neuro = NeurochemicalEngine()
    neuro.apply_stimulus(
        NeurochemicalStimulus(
            StimulusType.PROLONGED_ABSENCE,
            intensity=1.0,
        )
    )

    ctx_soon = ProactiveContext(
        now=_dt(20),
        neuro_state=neuro.state(),
        last_user_interaction_at=_dt(19, minute=30),
    )
    assert (
        NeurochemicalSignalGenerator().generate(ctx_soon)
        == []
    )

    ctx_long = ProactiveContext(
        now=_dt(20),
        neuro_state=neuro.state(),
        last_user_interaction_at=_dt(10),
    )
    signals = NeurochemicalSignalGenerator().generate(ctx_long)
    assert any(
        s.signal_type == "neurochemical:attachment"
        for s in signals
    )


def test_time_signal_evening_after_long_absence():
    ctx = ProactiveContext(
        now=_dt(22),
        last_user_interaction_at=_dt(9),
        current_slot_id="home_leisure",
    )

    signals = TimeSignalGenerator().generate(ctx)

    assert any(
        s.signal_type == "time:long_absence"
        for s in signals
    )


def test_time_signal_skips_when_recent_interaction():
    ctx = ProactiveContext(
        now=_dt(22),
        last_user_interaction_at=_dt(21, minute=50),
        current_slot_id="home_leisure",
    )

    assert TimeSignalGenerator().generate(ctx) == []


def test_memory_signal_respects_cooldown():
    gen = MemorySignalGenerator(cooldown_days=3.0)

    interest = type(
        "Interest",
        (),
        {
            "interest_id": "i:1",
            "content": "服务器部署",
            "importance": 0.9,
        },
    )()

    ctx1 = ProactiveContext(
        now=_dt(20, day=21),
        interests=[interest],
    )
    first = gen.generate(ctx1)
    assert len(first) == 1

    ctx2 = ProactiveContext(
        now=_dt(22, day=21),
        interests=[interest],
    )
    assert gen.generate(ctx2) == []

    ctx3 = ProactiveContext(
        now=_dt(22, day=24),
        interests=[interest],
    )
    assert len(gen.generate(ctx3)) == 1


# ---------------------------------------------------------
# ProactiveGate
# ---------------------------------------------------------


def test_gate_blocks_during_sleep_slot():
    gate = ProactiveGate()
    signal = ProactiveSignal(
        signal_type="test",
        reason="test",
        score=0.8,
        suggested_action="chat",
    )

    ctx = ProactiveContext(
        now=_dt(1),
        current_slot_id="sleep",
    )
    assert not gate.decide(ctx, signal)


def test_gate_blocks_late_night():
    gate = ProactiveGate()
    signal = ProactiveSignal(
        signal_type="test",
        reason="test",
        score=0.8,
        suggested_action="chat",
    )

    ctx = ProactiveContext(
        now=_dt(23),
        current_slot_id="home_leisure",
    )
    assert not gate.decide(ctx, signal)


def test_gate_respects_cooldown():
    gate = ProactiveGate(cooldown_minutes=60)
    signal = ProactiveSignal(
        signal_type="test",
        reason="test",
        score=0.8,
        suggested_action="chat",
    )

    ctx1 = ProactiveContext(
        now=_dt(20),
        current_slot_id="home_leisure",
    )
    assert gate.decide(ctx1, signal)
    gate.record_trigger(_dt(20))

    ctx2 = ProactiveContext(
        now=_dt(20, minute=30),
        current_slot_id="home_leisure",
    )
    assert not gate.decide(ctx2, signal)

    ctx3 = ProactiveContext(
        now=_dt(21),
        current_slot_id="home_leisure",
    )
    assert gate.decide(ctx3, signal)


def test_gate_blocks_low_energy():
    gate = ProactiveGate()
    signal = ProactiveSignal(
        signal_type="test",
        reason="test",
        score=0.8,
        suggested_action="chat",
    )

    class _LowEnergy:
        energy = 0.1

    ctx = ProactiveContext(
        now=_dt(20),
        life_state=_LowEnergy(),
        current_slot_id="home_leisure",
    )
    assert not gate.decide(ctx, signal)


# ---------------------------------------------------------
# UnifiedProactiveEngine
# ---------------------------------------------------------


def test_engine_returns_proactive_action():
    emotion = EmotionEngine()
    emotion.apply_event(EmotionEvent(EmotionType.LONELY, 1.0))

    engine = UnifiedProactiveEngine(
        gate=ProactiveGate(cooldown_minutes=0),
        max_actions=1,
    )

    ctx = ProactiveContext(
        now=_dt(20),
        emotion_state=emotion.state(),
        life_state=_FakeLifeState(),
        current_slot_id="home_leisure",
    )

    actions = engine.evaluate(ctx)

    assert len(actions) == 1
    action = actions[0]
    assert action.content == action.message
    assert action.signal.suggested_action in (
        "chat",
        "comfort",
        "share",
    )
    assert isinstance(action.source_interest_id, str)


def test_engine_empty_when_gated():
    engine = UnifiedProactiveEngine(
        gate=ProactiveGate(cooldown_minutes=0),
    )

    ctx = ProactiveContext(
        now=_dt(1),
        current_slot_id="sleep",
    )

    assert engine.evaluate(ctx) == []


def test_engine_message_for_remind():
    engine = UnifiedProactiveEngine()

    interest = type(
        "Interest",
        (),
        {
            "interest_id": "i:2",
            "content": "项目进展",
            "importance": 0.9,
        },
    )()

    ctx = ProactiveContext(
        now=_dt(20),
        interests=[interest],
        life_state=_FakeLifeState(),
        current_slot_id="home_leisure",
    )

    actions = engine.evaluate(ctx)

    assert len(actions) == 1
    assert "项目进展" in actions[0].message


def test_engine_builds_chat_message_for_lonely():
    emotion = EmotionEngine()
    emotion.apply_event(EmotionEvent(EmotionType.LONELY, 1.0))

    engine = UnifiedProactiveEngine(
        gate=ProactiveGate(cooldown_minutes=0),
        max_actions=1,
    )

    ctx = ProactiveContext(
        now=_dt(20),
        emotion_state=emotion.state(),
        life_state=_FakeLifeState(),
        current_slot_id="home_leisure",
    )

    actions = engine.evaluate(ctx)
    assert any(
        "好久没出现了" in a.message
        for a in actions
    ) or actions


def test_signal_rejects_invalid_action():
    with pytest.raises(ValueError):
        ProactiveSignal(
            signal_type="test",
            reason="test",
            score=0.8,
            suggested_action="bogus",
        )
