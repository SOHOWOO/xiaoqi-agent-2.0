import json
from datetime import timedelta

import pytest

from core.emotion import EmotionState
from core.life_loop import LifeLoop
from core.neurochemical import NeurochemicalState
from core.time_engine import make_aware
from life_lab.logger import SimulationLogger
from life_lab.metrics import HealthMetrics
from life_lab.reporter import Reporter
from life_lab.scenarios.lonely_week import LonelyWeekScenario


def _snapshot(
    *,
    time,
    energy=0.7,
    fatigue=0.5,
    lonely=0.1,
) -> dict:
    return {
        "time": time,
        "life": {
            "current_activity": "test",
            "energy": energy,
            "fatigue": fatigue,
        },
        "emotion": EmotionState(
            happy=0.2,
            lonely=lonely,
            excited=0.1,
            anxious=0.1,
            angry=0.05,
            calm=0.6,
        ),
        "neurochemical": NeurochemicalState(
            dopamine=0.45,
            serotonin=0.55,
            oxytocin=0.35,
            cortisol=0.25,
            endorphin=0.3,
            noradrenaline=0.4,
        ),
        "relationship": {
            "trust": 0.2,
            "attachment": 0.2,
            "familiarity": 0.0,
            "shared_experience": 0.0,
            "interaction_count": 0,
            "last_interaction_at": None,
        },
        "memory": {"count": 1, "diary_count": 1},
    }


def test_lonely_week_scenario_params():
    scenario = LonelyWeekScenario()

    assert scenario.name == "lonely_week"
    assert scenario.steps() == 7 * 24 * 4
    assert scenario.tick_minutes() == 15
    assert scenario.duration() == timedelta(days=7)


def test_logger_writes_jsonl(tmp_path):
    logger = SimulationLogger(tmp_path / "exp")
    start = make_aware(2026, 8, 22, 8, 0)

    logger.record(_snapshot(time=start))
    logger.record(_snapshot(time=start + timedelta(minutes=15)))

    assert logger.count == 2
    assert (tmp_path / "exp" / "state.jsonl").exists()

    lines = (
        tmp_path / "exp" / "state.jsonl"
    ).read_text(encoding="utf-8").strip().splitlines()

    assert len(lines) == 2

    first = json.loads(lines[0])
    assert first["time"].startswith("2026-08-22")
    assert "energy" in first["life"]
    assert "happy" in first["emotion"]
    assert "dopamine" in first["neurochemical"]


def test_metrics_all_pass():
    start = make_aware(2026, 8, 22, 8, 0)

    records = [
        _snapshot(time=start + timedelta(minutes=15 * i), lonely=i * 0.01)
        for i in range(5)
    ]
    records[1]["life"]["energy"] = 0.9
    records[2]["life"]["energy"] = 0.5
    records[-1]["relationship"]["attachment"] = 0.19

    metrics = HealthMetrics().check(records, expected_steps=5)

    assert metrics["completed"] is True
    assert metrics["energy_in_range"] is True
    assert metrics["energy_varies"] is True
    assert metrics["emotion_varies"] is True
    assert metrics["relationship_varies"] is True
    assert metrics["relationship_valid"] is True


def test_metrics_detects_incomplete():
    start = make_aware(2026, 8, 22, 8, 0)
    records = [_snapshot(time=start)]

    metrics = HealthMetrics().check(records, expected_steps=672)

    assert metrics["completed"] is False


def test_metrics_detects_energy_out_of_range():
    start = make_aware(2026, 8, 22, 8, 0)
    records = [_snapshot(time=start, energy=1.5)]

    metrics = HealthMetrics().check(records, expected_steps=1)

    assert metrics["energy_in_range"] is False


def test_reporter_pass_and_fail(capsys):
    reporter = Reporter()

    ok_metrics = {
        "completed": True,
        "energy_in_range": True,
        "energy_varies": True,
        "emotion_varies": True,
        "relationship_varies": True,
        "relationship_valid": True,
    }

    assert reporter.report(
        ok_metrics,
        run_id="x",
        folder="f",
        name="lonely_week",
    ) is True

    bad_metrics = dict(ok_metrics)
    bad_metrics["completed"] = False

    assert reporter.report(
        bad_metrics,
        run_id="x",
        folder="f",
        name="lonely_week",
    ) is False


def test_runner_runs_short_experiment():
    """跑一小段（1 天）实验，验证 runner 链路完整。"""

    from datetime import datetime

    from life_lab.runner import run as _runner

    import life_lab.runner as runner_module

    class _ShortScenario:
        name = "short_test"

        def start(self):
            return make_aware(2026, 8, 22, 8, 0)

        def duration(self):
            return timedelta(days=3)

        def tick_minutes(self):
            return 60

        def seed(self):
            return 42

        def steps(self):
            return int(
                self.duration().total_seconds()
                / (self.tick_minutes() * 60)
            )

        def step(self, life):
            return None

    original = runner_module.LonelyWeekScenario
    runner_module.LonelyWeekScenario = _ShortScenario

    try:
        ok = _runner()
    finally:
        runner_module.LonelyWeekScenario = original

    assert ok is True
