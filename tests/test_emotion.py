from datetime import datetime

import pytest

from core.emotion import (
    EMOTION_BASELINE,
    EmotionEngine,
    EmotionEvent,
    EmotionState,
    EmotionType,
    SQLiteEmotionStore,
    map_neurochemical_to_emotions,
)
from core.neurochemical import (
    NeurochemicalEngine,
    NeurochemicalStimulus,
    StimulusType,
)


def test_initial_state_equals_baseline():
    engine = EmotionEngine()
    state = engine.state()

    for e in EmotionType:
        assert state.level(e) == pytest.approx(
            EMOTION_BASELINE[e]
        )


def test_dominant_is_calm_by_default():
    engine = EmotionEngine()

    assert engine.dominant_emotion() == EmotionType.CALM


def test_apply_event_boosts_target_and_lowers_inverse():
    engine = EmotionEngine()

    engine.apply_event(
        EmotionEvent(EmotionType.HAPPY, 0.8)
    )

    assert engine.state().happy > EMOTION_BASELINE[
        EmotionType.HAPPY
    ]
    assert engine.state().lonely < EMOTION_BASELINE[
        EmotionType.LONELY
    ]


def test_tick_regresses_to_baseline():
    engine = EmotionEngine()
    engine.apply_event(
        EmotionEvent(EmotionType.ANGRY, 1.0)
    )

    assert engine.state().angry > EMOTION_BASELINE[
        EmotionType.ANGRY
    ]

    engine.tick(hours=100.0)

    state = engine.state()
    for e in EmotionType:
        assert state.level(e) == pytest.approx(
            EMOTION_BASELINE[e],
            abs=1e-6,
        )


def test_update_from_neurochemical_moves_toward_target():
    neuro = NeurochemicalEngine()
    neuro.apply_stimulus(
        NeurochemicalStimulus(
            StimulusType.ACHIEVEMENT,
            intensity=1.0,
        )
    )

    engine = EmotionEngine()
    before_happy = engine.state().happy

    engine.update_from_neurochemical(neuro.state())

    target = map_neurochemical_to_emotions(neuro.state())
    assert target.happy > before_happy
    assert engine.state().happy > before_happy
    assert engine.state().happy <= target.happy


def test_neurochemical_mapping_high_cortisol_raises_anxiety():
    neuro = NeurochemicalEngine()
    neuro.apply_stimulus(
        NeurochemicalStimulus(
            StimulusType.CONFLICT,
            intensity=1.0,
        )
    )

    baseline = map_neurochemical_to_emotions(
        NeurochemicalEngine().state()
    )
    stressed = map_neurochemical_to_emotions(neuro.state())

    assert stressed.anxious > baseline.anxious
    assert stressed.angry > baseline.angry


def test_neurochemical_mapping_low_oxytocin_raises_loneliness():
    neuro = NeurochemicalEngine()
    neuro.apply_stimulus(
        NeurochemicalStimulus(
            StimulusType.PROLONGED_ABSENCE,
            intensity=1.0,
        )
    )

    baseline = map_neurochemical_to_emotions(
        NeurochemicalEngine().state()
    )
    absent = map_neurochemical_to_emotions(neuro.state())

    assert absent.lonely > baseline.lonely


def test_valence_and_arousal_bounds():
    engine = EmotionEngine()

    assert 0.0 <= engine.valence() <= 1.0
    assert 0.0 <= engine.arousal() <= 1.0


def test_apply_event_increases_arousal_when_excited():
    engine = EmotionEngine()
    before = engine.arousal()

    engine.apply_event(
        EmotionEvent(EmotionType.EXCITED, 1.0)
    )

    assert engine.arousal() > before


def test_tick_rejects_negative_hours():
    engine = EmotionEngine()

    with pytest.raises(ValueError):
        engine.tick(hours=-1.0)


def test_invalid_state_values_rejected():
    with pytest.raises(ValueError):
        EmotionState(
            happy=1.5,
            lonely=0.1,
            excited=0.1,
            anxious=0.1,
            angry=0.1,
            calm=0.1,
        )


def test_invalid_event_intensity_rejected():
    with pytest.raises(ValueError):
        EmotionEvent(EmotionType.HAPPY, 1.5)


def test_restore_and_reset():
    engine = EmotionEngine()
    engine.apply_event(
        EmotionEvent(EmotionType.EXCITED, 1.0)
    )
    excited = engine.state()

    engine.reset()
    assert engine.state() == EmotionEngine().state()

    engine.restore(excited)
    assert engine.state() == excited


def test_sqlite_round_trip(tmp_path):
    db = tmp_path / "emotion.db"
    store = SQLiteEmotionStore(db)

    engine = EmotionEngine()
    engine.apply_event(
        EmotionEvent(EmotionType.HAPPY, 1.0)
    )
    state = engine.state()

    store.save(
        state,
        updated_at=datetime(2026, 8, 22, 10, 0),
    )

    assert store.load() == state

    store.close()


def test_sqlite_load_empty_returns_none(tmp_path):
    db = tmp_path / "emotion.db"
    store = SQLiteEmotionStore(db)

    assert store.load() is None

    store.close()


def test_sqlite_overwrites_previous(tmp_path):
    db = tmp_path / "emotion.db"
    store = SQLiteEmotionStore(db)

    first = EmotionEngine().state()
    engine = EmotionEngine()
    engine.apply_event(
        EmotionEvent(EmotionType.ANGRY, 1.0)
    )
    second = engine.state()

    store.save(first)
    store.save(second)

    assert store.load() == second

    store.close()
