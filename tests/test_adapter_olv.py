import asyncio
from datetime import datetime

import pytest

from core.adapters.openllm_vtuber import (
    Actions,
    BatchInput,
    DisplayText,
    SentenceOutput,
    TextData,
    TextSource,
    XiaoqiAgent,
    XiaoqiBusBridge,
    create_xiaoqi_agent,
    map_emotion_to_expression,
)
from core.chat import StubResponseProvider
from core.emotion import EmotionEvent, EmotionType
from core.life_loop import LifeLoop
from core.memory import SQLiteMemoryStore
from core.time_engine import DEFAULT_TZ


def _agent(tmp_path):
    store = SQLiteMemoryStore(tmp_path / "mem.db")
    life = LifeLoop(
        start_time=datetime(2026, 8, 22, 8, 0, tzinfo=DEFAULT_TZ),
        seed=42,
        memory_store=store,
    )
    agent = create_xiaoqi_agent(
        life_loop=life,
        response_provider=StubResponseProvider(),
    )
    return agent, life


def _run(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


async def _collect(agent, input_data):
    outputs = []
    async for out in agent.chat(input_data):
        outputs.append(out)
    return outputs


def test_emotion_map():
    assert map_emotion_to_expression("happy") == "happy"
    assert map_emotion_to_expression("angry") == "angry"
    assert map_emotion_to_expression("lonely") == "sad"
    assert map_emotion_to_expression("calm") == "neutral"
    assert map_emotion_to_expression("unknown") == "neutral"


def test_chat_returns_sentence_output(tmp_path):
    agent, life = _agent(tmp_path)

    input_data = BatchInput(
        texts=[TextData(source=TextSource.INPUT, content="你好")]
    )

    outputs = _run(_collect(agent, input_data))

    assert len(outputs) == 1
    out = outputs[0]
    assert isinstance(out, SentenceOutput)
    assert out.display_text.name == "小七"
    assert out.tts_text
    assert out.actions.expressions


def test_chat_output_contains_emotion_expression(tmp_path):
    agent, life = _agent(tmp_path)

    # 制造开心情绪
    life.emotion.apply_event(EmotionEvent(EmotionType.HAPPY, 1.0))

    input_data = BatchInput(
        texts=[TextData(source=TextSource.INPUT, content="哈哈")]
    )

    outputs = _run(_collect(agent, input_data))

    expr = outputs[0].actions.expressions[0]
    assert expr == "happy"


def test_chat_proactive_speak(tmp_path):
    agent, life = _agent(tmp_path)

    # 制造失联 -> 主动消息入队
    from datetime import timedelta

    life.emotion.apply_event(EmotionEvent(EmotionType.LONELY, 1.0))
    life.tick(timedelta(minutes=15))

    pending = life.get_pending_proactive_messages()
    assert pending  # 应有主动消息

    # 塞回 pending（模拟待发送）
    for msg in pending:
        life._pending_proactive_messages.append(msg)

    input_data = BatchInput(
        texts=[],
        metadata={"proactive_speak": True},
    )

    outputs = _run(_collect(agent, input_data))

    assert len(outputs) >= 1
    assert outputs[0].display_text.text


def test_chat_empty_input_returns_nothing(tmp_path):
    agent, _ = _agent(tmp_path)

    input_data = BatchInput(
        texts=[TextData(source=TextSource.INPUT, content="   ")]
    )

    outputs = _run(_collect(agent, input_data))

    assert outputs == []


def test_handle_interrupt_records_and_clears_pending(tmp_path):
    agent, life = _agent(tmp_path)

    from datetime import timedelta

    life.emotion.apply_event(EmotionEvent(EmotionType.LONELY, 1.0))
    life.tick(timedelta(minutes=15))
    pending = life.get_pending_proactive_messages()
    for msg in pending:
        life._pending_proactive_messages.append(msg)

    agent.handle_interrupt("还没说完")

    assert agent._interrupted is True
    assert agent.interrupts
    assert life.get_pending_proactive_messages() == []


def test_set_memory_from_history(tmp_path):
    agent, _ = _agent(tmp_path)

    agent.set_memory_from_history("conf-1", "hist-1")

    assert agent._history_ref == ("conf-1", "hist-1")


def test_bus_bridge_emotion_change(tmp_path):
    agent, life = _agent(tmp_path)

    # 先发布一次基线（calm），之后的变化才会触发 emotion_change
    life._publish_engine_events(
        life.current_time,
        diary_entry=None,
    )

    bridge = XiaoqiBusBridge(life.event_bus)

    life.emotion.apply_event(EmotionEvent(EmotionType.ANGRY, 1.0))
    life._publish_engine_events(
        life.current_time,
        diary_entry=None,
    )

    assert bridge.last_emotion == "angry"
    payload = bridge.expression_payload()
    assert payload["expressions"] == ["angry"]


def test_bus_bridge_proactive(tmp_path):
    agent, life = _agent(tmp_path)

    bridge = XiaoqiBusBridge(life.event_bus)

    from datetime import timedelta

    life.emotion.apply_event(EmotionEvent(EmotionType.LONELY, 1.0))
    life.tick(timedelta(minutes=15))

    assert bridge.last_proactive is not None
    payload = bridge.proactive_payload()
    assert payload["proactive_speak"] is True


def test_sentence_output_iteration():
    out = SentenceOutput(
        display_text=DisplayText(text="hi", name="小七"),
        tts_text="hi",
        actions=Actions(expressions=["neutral"]),
    )

    async def collect():
        return [x async for x in out]

    items = asyncio.get_event_loop().run_until_complete(collect())
    assert len(items) == 1
