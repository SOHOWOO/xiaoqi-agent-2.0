from datetime import timedelta

from core.life_loop import LifeLoop
from core.time_engine import make_aware


def _loop():
    start = make_aware(2026, 8, 22, 8, 0)
    return LifeLoop(start_time=start, seed=42)


def test_receive_positive_interaction_grows_relationship():
    life = _loop()

    baseline = life.relationship_engine.state.attachment

    life.receive_event(
        {
            "type": "positive_interaction",
            "intensity": 1.0,
            "message": "今天陪小七学习",
        }
    )

    assert (
        life.relationship_engine.state.attachment
        > baseline
    )
    assert (
        life.relationship_engine.state.trust
        > baseline
    )


def test_receive_conflict_erodes_trust_and_raises_tension():
    life = _loop()

    life.receive_event({"type": "positive_interaction", "intensity": 1.0})
    peak = life.relationship_engine.state.trust

    life.receive_event(
        {
            "type": "conflict",
            "severity": 0.5,
            "message": "感觉你最近不理解我",
        }
    )

    assert life.relationship_engine.state.trust < peak

    emotion = life.emotion.state()
    assert emotion.angry > 0.2
    assert emotion.anxious > 0.2


def test_receive_event_records_episodic_memory():
    from core.memory import MemoryType

    life = _loop()

    life.receive_event(
        {"type": "comfort", "message": "别难过，我在"}
    )

    episodic = life.memory_store.by_type(MemoryType.EPISODIC)

    assert len(episodic) == 1
    assert "别难过" in episodic[0].content


def test_receive_event_sets_interaction_time():
    life = _loop()

    life.tick(timedelta(hours=2))
    life.receive_event({"type": "positive_interaction"})

    assert (
        life.interaction_state.last_user_interaction_at
        == life.current_time
    )


def test_get_actions_readonly_does_not_consume_gate():
    life = _loop()

    # 制造失联，产生主动动机
    for _ in range(3 * 24 * 4):
        life.tick(timedelta(minutes=15))

    # 清除 pending 消息（它们是 tick 中已触发入队的）
    life.get_pending_proactive_messages()

    actions1 = life.get_actions()
    actions2 = life.get_actions()

    # 只读评估：连续调用不应改变结果（不消耗冷却）
    assert len(actions1) == len(actions2)

    # 且不产生 pending 消息（peek 不触发）
    assert life.get_pending_proactive_messages() == []


def test_get_actions_returns_actions_with_message():
    life = _loop()

    for _ in range(3 * 24 * 4):
        life.tick(timedelta(minutes=15))

    actions = life.get_actions()

    for action in actions:
        assert action.message
        assert action.signal.suggested_action in (
            "chat",
            "comfort",
            "share",
            "remind",
            "play",
        )
