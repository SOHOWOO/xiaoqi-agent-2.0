from datetime import datetime

from core.memory import MemoryStore
from core.memory.manager import MemoryAction, MemoryManager
from core.memory.models import MemoryRecord, MemorySource, MemoryType


def make_memory(
    memory_id: str,
    memory_type: MemoryType,
    content: str,
    importance: float = 1.0,
) -> MemoryRecord:
    return MemoryRecord(
        memory_id=memory_id,
        memory_type=memory_type,
        content=content,
        importance=importance,
        created_at=datetime(2026, 8, 20, 14, 0),
        source=MemorySource.USER_PROVIDED,
    )


def test_canonical_new_memory_is_added():
    store = MemoryStore()
    manager = MemoryManager(store)

    memory = make_memory(
        "canonical:new",
        MemoryType.CANONICAL,
        "姓名：小七",
    )

    decision = manager.decide(memory)

    assert decision.action == MemoryAction.ADD


def test_canonical_can_update_canonical():
    store = MemoryStore()
    manager = MemoryManager(store)

    target = make_memory(
        "canonical:old",
        MemoryType.CANONICAL,
        "年龄：24岁",
    )

    memory = make_memory(
        "canonical:new",
        MemoryType.CANONICAL,
        "年龄：25岁",
    )

    decision = manager.decide(memory, target)

    assert decision.action == MemoryAction.UPDATE
    assert decision.target_memory_id == "canonical:old"


def test_low_importance_interaction_is_ignored():
    store = MemoryStore()
    manager = MemoryManager(store)

    memory = make_memory(
        "interaction:low",
        MemoryType.INTERACTION,
        "今天随口聊到天气",
        importance=0.3,
    )

    decision = manager.decide(memory)

    assert decision.action == MemoryAction.IGNORE


def test_high_importance_interaction_is_added():
    store = MemoryStore()
    manager = MemoryManager(store)

    memory = make_memory(
        "interaction:high",
        MemoryType.INTERACTION,
        "用户明确表示喜欢咖啡",
        importance=0.9,
    )

    decision = manager.decide(memory)

    assert decision.action == MemoryAction.ADD


def test_virtual_life_cannot_modify_canonical():
    store = MemoryStore()
    manager = MemoryManager(store)

    target = make_memory(
        "canonical:identity",
        MemoryType.CANONICAL,
        "真实身份：小七",
    )

    memory = make_memory(
        "virtual:identity",
        MemoryType.VIRTUAL_LIFE,
        "虚拟生活设定",
        importance=0.9,
    )

    decision = manager.decide(memory, target)

    assert decision.action == MemoryAction.REJECT
    assert decision.target_memory_id == "canonical:identity"


def test_interaction_cannot_modify_canonical():
    store = MemoryStore()
    manager = MemoryManager(store)

    target = make_memory(
        "canonical:identity",
        MemoryType.CANONICAL,
        "真实身份：小七",
    )

    memory = make_memory(
        "interaction:identity",
        MemoryType.INTERACTION,
        "聊天中说小七是另一个人",
        importance=0.9,
    )

    decision = manager.decide(memory, target)

    assert decision.action == MemoryAction.REJECT
    assert decision.target_memory_id == "canonical:identity"


def test_interaction_can_update_interaction():
    store = MemoryStore()
    manager = MemoryManager(store)

    target = make_memory(
        "interaction:old",
        MemoryType.INTERACTION,
        "用户最近喜欢喝茶",
    )

    memory = make_memory(
        "interaction:new",
        MemoryType.INTERACTION,
        "用户最近更喜欢喝咖啡",
        importance=0.9,
    )

    decision = manager.decide(memory, target)

    assert decision.action == MemoryAction.UPDATE
    assert decision.target_memory_id == "interaction:old"


def test_virtual_life_can_update_virtual_life():
    store = MemoryStore()
    manager = MemoryManager(store)

    target = make_memory(
        "virtual:old",
        MemoryType.VIRTUAL_LIFE,
        "旧的虚拟生活设定",
    )

    memory = make_memory(
        "virtual:new",
        MemoryType.VIRTUAL_LIFE,
        "新的虚拟生活设定",
        importance=0.9,
    )

    decision = manager.decide(memory, target)

    assert decision.action == MemoryAction.UPDATE
    assert decision.target_memory_id == "virtual:old"


def test_add_if_allowed_only_adds_on_add():
    store = MemoryStore()
    manager = MemoryManager(store)

    canonical = make_memory(
        "canonical:add",
        MemoryType.CANONICAL,
        "姓名：小七",
    )

    decision = manager.add_if_allowed(canonical)

    assert decision.action == MemoryAction.ADD
    assert len(store) == 1


def test_add_if_allowed_ignores_low_importance_memory():
    store = MemoryStore()
    manager = MemoryManager(store)

    memory = make_memory(
        "interaction:ignore",
        MemoryType.INTERACTION,
        "随口提到天气",
        importance=0.2,
    )

    decision = manager.add_if_allowed(memory)

    assert decision.action == MemoryAction.IGNORE
    assert len(store) == 0
def test_update_if_allowed_replaces_existing_memory():
    store = MemoryStore()
    manager = MemoryManager(store)

    old = make_memory(
        "interaction:preference",
        MemoryType.INTERACTION,
        "用户喜欢喝茶",
        importance=0.9,
    )

    store.add(old)

    new = make_memory(
        "interaction:new",
        MemoryType.INTERACTION,
        "用户现在更喜欢喝咖啡",
        importance=0.9,
    )

    decision = manager.update_if_allowed(
        new,
        old,
    )

    assert decision.action == MemoryAction.UPDATE
    assert decision.target_memory_id == old.memory_id
    assert len(store) == 1

    updated = store.get("interaction:preference")

    assert updated is not None
    assert updated.content == "用户现在更喜欢喝咖啡"
    assert updated.memory_id == "interaction:preference"


def test_rejected_update_does_not_change_memory():
    store = MemoryStore()
    manager = MemoryManager(store)

    old = make_memory(
        "canonical:identity",
        MemoryType.CANONICAL,
        "真实身份：小七",
    )

    store.add(old)

    new = make_memory(
        "virtual:identity",
        MemoryType.VIRTUAL_LIFE,
        "虚拟生活身份",
        importance=1.0,
    )

    decision = manager.update_if_allowed(
        new,
        old,
    )

    assert decision.action == MemoryAction.REJECT

    stored = store.get("canonical:identity")

    assert stored is not None
    assert stored.content == "真实身份：小七"
def test_store_update_replaces_record():
    store = MemoryStore()

    old = make_memory(
        "memory:1",
        MemoryType.INTERACTION,
        "旧内容",
    )

    store.add(old)

    new = make_memory(
        "memory:new",
        MemoryType.INTERACTION,
        "新内容",
    )

    updated = store.update(
        "memory:1",
        new,
    )

    assert updated.memory_id == "memory:1"
    assert updated.content == "新内容"
    assert len(store) == 1