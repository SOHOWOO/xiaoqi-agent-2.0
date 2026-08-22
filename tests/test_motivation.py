from datetime import datetime

import pytest

from core.emotion import (
    EmotionEngine,
    EmotionEvent,
    EmotionType,
)
from core.motivation import (
    ActionPlanner,
    Motivation,
    MotivationEngine,
    MotivationType,
)
from core.neurochemical import (
    NeurochemicalEngine,
    NeurochemicalStimulus,
    StimulusType,
)
from core.proactive import ProactiveContext
from core.time_engine import DEFAULT_TZ


def _dt(hour: int, day: int = 22) -> datetime:
    return datetime(2026, 8, day, hour, 0, tzinfo=DEFAULT_TZ)


class _FakeLifeState:
    energy = 0.8


def _lonely_ctx():
    emotion = EmotionEngine()
    emotion.apply_event(EmotionEvent(EmotionType.LONELY, 1.0))

    return ProactiveContext(
        now=_dt(20),
        emotion_state=emotion.state(),
    )


def test_craving_contact_from_loneliness():
    engine = MotivationEngine()

    motivations = engine.evaluate(_lonely_ctx())

    assert any(
        m.type == MotivationType.CRAVING_CONTACT
        for m in motivations
    )


def test_craving_contact_from_attachment_and_absence():
    neuro = NeurochemicalEngine()
    neuro.apply_stimulus(
        NeurochemicalStimulus(
            StimulusType.PROLONGED_ABSENCE,
            intensity=1.0,
        )
    )

    ctx = ProactiveContext(
        now=_dt(20),
        neuro_state=neuro.state(),
        last_user_interaction_at=_dt(10),
    )

    motivations = MotivationEngine().evaluate(ctx)

    assert any(
        m.type == MotivationType.CRAVING_CONTACT
        for m in motivations
    )


def test_comfort_from_anxiety():
    emotion = EmotionEngine()
    emotion.apply_event(EmotionEvent(EmotionType.ANXIOUS, 1.0))

    ctx = ProactiveContext(
        now=_dt(20),
        emotion_state=emotion.state(),
    )

    motivations = MotivationEngine().evaluate(ctx)

    assert any(
        m.type == MotivationType.COMFORT
        for m in motivations
    )


def test_remind_from_interests():
    interest = type(
        "Interest",
        (),
        {
            "interest_id": "i:1",
            "content": "项目进展",
            "importance": 0.9,
        },
    )()

    ctx = ProactiveContext(
        now=_dt(20),
        interests=[interest],
    )

    motivations = MotivationEngine().evaluate(ctx)

    remind = [
        m for m in motivations
        if m.type == MotivationType.REMIND
    ]
    assert remind
    assert remind[0].payload == "项目进展"


def test_remind_respects_cooldown():
    interest = type(
        "Interest",
        (),
        {
            "interest_id": "i:1",
            "content": "项目进展",
            "importance": 0.9,
        },
    )()

    engine = MotivationEngine()

    ctx1 = ProactiveContext(now=_dt(20, day=21), interests=[interest])
    assert engine.evaluate(ctx1)

    ctx2 = ProactiveContext(now=_dt(20, day=22), interests=[interest])
    assert not any(
        m.type == MotivationType.REMIND
        for m in engine.evaluate(ctx2)
    )

    ctx3 = ProactiveContext(now=_dt(20, day=25), interests=[interest])
    assert any(
        m.type == MotivationType.REMIND
        for m in engine.evaluate(ctx3)
    )


def test_play_from_boredom():
    neuro = NeurochemicalEngine()

    ctx = ProactiveContext(
        now=_dt(20),
        neuro_state=neuro.state(),
        life_state=_FakeLifeState(),
    )

    # 默认 dopamine 0.45 >= 0.3，不无聊
    assert not any(
        m.type == MotivationType.PLAY
        for m in MotivationEngine().evaluate(ctx)
    )

    # 通过刺激降低... 构造低多巴胺：直接构造状态
    from core.neurochemical import NeurochemicalState

    bored = NeurochemicalState(
        dopamine=0.1,
        serotonin=0.5,
        oxytocin=0.4,
        cortisol=0.2,
        endorphin=0.3,
        noradrenaline=0.3,
    )

    ctx_bored = ProactiveContext(
        now=_dt(20),
        neuro_state=bored,
        life_state=_FakeLifeState(),
    )

    assert any(
        m.type == MotivationType.PLAY
        for m in MotivationEngine().evaluate(ctx_bored)
    )


def test_motivations_sorted_by_intensity():
    ctx = _lonely_ctx()

    # 同时孤独 + 焦虑
    ctx.emotion_state = _lonely_ctx().emotion_state
    emotion = EmotionEngine()
    emotion.apply_event(EmotionEvent(EmotionType.LONELY, 1.0))
    emotion.apply_event(EmotionEvent(EmotionType.ANXIOUS, 0.9))
    ctx.emotion_state = emotion.state()

    motivations = MotivationEngine().evaluate(ctx)

    intensities = [m.intensity for m in motivations]
    assert intensities == sorted(
        intensities,
        reverse=True,
    )


def test_planner_maps_motivation_to_signal():
    planner = ActionPlanner()
    motivation = Motivation(
        type=MotivationType.CRAVING_CONTACT,
        intensity=0.8,
        reasons=("小七想主人了",),
    )

    signals = planner.plan([motivation], _lonely_ctx())

    assert len(signals) == 1
    assert signals[0].suggested_action == "chat"
    assert signals[0].score == 0.8
    assert signals[0].signal_type == "motivation:craving_contact"


def test_motivation_validates_intensity():
    with pytest.raises(ValueError):
        Motivation(
            type=MotivationType.SHARE,
            intensity=1.5,
        )
