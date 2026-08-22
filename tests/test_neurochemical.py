from datetime import datetime

import pytest

from core.neurochemical import (
    DEFAULT_PROFILES,
    NeurochemicalEngine,
    NeurochemicalState,
    NeurochemicalStimulus,
    Neurotransmitter,
    SQLiteNeurochemicalStore,
    StimulusType,
)


def test_initial_state_equals_baselines():
    engine = NeurochemicalEngine()

    state = engine.state()

    for nt in Neurotransmitter:
        profile = DEFAULT_PROFILES[nt]
        assert state.level(nt) == pytest.approx(
            profile.baseline
        )


def test_tick_decays_toward_baseline():
    engine = NeurochemicalEngine()
    engine.apply_stimulus(
        NeurochemicalStimulus(
            StimulusType.ACHIEVEMENT,
            intensity=1.0,
        )
    )

    boosted = engine.state()
    assert boosted.dopamine > DEFAULT_PROFILES[
        Neurotransmitter.DOPAMINE
    ].baseline

    engine.tick(hours=100.0)

    settled = engine.state()
    for nt in Neurotransmitter:
        assert settled.level(nt) == pytest.approx(
            DEFAULT_PROFILES[nt].baseline,
            abs=1e-6,
        )


def test_tick_does_not_cross_baseline():
    engine = NeurochemicalEngine()
    engine.apply_stimulus(
        NeurochemicalStimulus(
            StimulusType.USER_INTERACTION,
            intensity=1.0,
        )
    )

    engine.tick(hours=0.5)

    baseline = DEFAULT_PROFILES[
        Neurotransmitter.OXYTOCIN
    ].baseline
    assert engine.state().oxytocin >= baseline


def test_apply_stimulus_user_interaction():
    engine = NeurochemicalEngine()
    before = engine.state()

    engine.apply_stimulus(
        NeurochemicalStimulus(
            StimulusType.USER_INTERACTION,
            intensity=1.0,
        )
    )

    after = engine.state()

    assert after.oxytocin > before.oxytocin
    assert after.dopamine > before.dopamine
    assert after.cortisol < before.cortisol


def test_apply_stimulus_intensity_scales_effect():
    engine_low = NeurochemicalEngine()
    engine_high = NeurochemicalEngine()

    engine_low.apply_stimulus(
        NeurochemicalStimulus(StimulusType.CONFLICT, 0.2)
    )
    engine_high.apply_stimulus(
        NeurochemicalStimulus(StimulusType.CONFLICT, 1.0)
    )

    baseline = DEFAULT_PROFILES[
        Neurotransmitter.CORTISOL
    ].baseline

    low_delta = engine_low.state().cortisol - baseline
    high_delta = engine_high.state().cortisol - baseline

    assert high_delta > low_delta


def test_prolonged_absence_raises_attachment_drive():
    engine = NeurochemicalEngine()

    engine.apply_stimulus(
        NeurochemicalStimulus(
            StimulusType.PROLONGED_ABSENCE,
            intensity=1.0,
        )
    )

    baseline_drive = NeurochemicalEngine().attachment_drive()

    assert engine.attachment_drive() > baseline_drive


def test_state_is_clamped():
    engine = NeurochemicalEngine()

    for _ in range(10):
        engine.apply_stimulus(
            NeurochemicalStimulus(StimulusType.CONFLICT, 1.0)
        )

    state = engine.state()
    for nt in Neurotransmitter:
        assert 0.0 <= state.level(nt) <= 1.0


def test_derived_metrics_bounds():
    engine = NeurochemicalEngine()

    assert 0.0 <= engine.reward_signal() <= 1.0
    assert 0.0 <= engine.stress_level() <= 1.0
    assert 0.0 <= engine.attachment_drive() <= 1.0
    assert 0.0 <= engine.curiosity() <= 1.0
    assert 0.0 <= engine.mood_stability() <= 1.0


def test_tick_rejects_negative_hours():
    engine = NeurochemicalEngine()

    with pytest.raises(ValueError):
        engine.tick(hours=-1.0)


def test_invalid_state_values_rejected():
    with pytest.raises(ValueError):
        NeurochemicalState(
            dopamine=1.5,
            serotonin=0.5,
            oxytocin=0.5,
            cortisol=0.5,
            endorphin=0.5,
            noradrenaline=0.5,
        )


def test_invalid_intensity_rejected():
    with pytest.raises(ValueError):
        NeurochemicalStimulus(
            StimulusType.PRAISE,
            intensity=1.5,
        )


def test_restore_and_reset():
    engine = NeurochemicalEngine()
    engine.apply_stimulus(
        NeurochemicalStimulus(StimulusType.PRAISE, 1.0)
    )
    boosted = engine.state()

    engine.reset()
    assert engine.state() == NeurochemicalEngine().state()

    engine.restore(boosted)
    assert engine.state() == boosted


def test_sqlite_round_trip(tmp_path):
    db = tmp_path / "neuro.db"
    store = SQLiteNeurochemicalStore(db)

    engine = NeurochemicalEngine()
    engine.apply_stimulus(
        NeurochemicalStimulus(StimulusType.REST, 1.0)
    )
    state = engine.state()

    store.save(
        state,
        updated_at=datetime(2026, 8, 22, 10, 0),
    )

    loaded = store.load()
    assert loaded == state

    store.close()


def test_sqlite_load_empty_returns_none(tmp_path):
    db = tmp_path / "neuro.db"
    store = SQLiteNeurochemicalStore(db)

    assert store.load() is None

    store.close()


def test_sqlite_overwrites_previous(tmp_path):
    db = tmp_path / "neuro.db"
    store = SQLiteNeurochemicalStore(db)

    first = NeurochemicalEngine().state()
    engine = NeurochemicalEngine()
    engine.apply_stimulus(
        NeurochemicalStimulus(StimulusType.ACHIEVEMENT, 1.0)
    )
    second = engine.state()

    store.save(first)
    store.save(second)

    assert store.load() == second

    store.close()
