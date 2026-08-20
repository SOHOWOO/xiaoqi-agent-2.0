from core.memory.models import MemoryType
from core.memory.policy import can_modify, is_long_term_candidate


def test_virtual_life_cannot_modify_canonical():
    assert not can_modify(
        MemoryType.VIRTUAL_LIFE,
        MemoryType.CANONICAL,
    )


def test_interaction_cannot_modify_canonical():
    assert not can_modify(
        MemoryType.INTERACTION,
        MemoryType.CANONICAL,
    )


def test_canonical_can_modify_canonical():
    assert can_modify(
        MemoryType.CANONICAL,
        MemoryType.CANONICAL,
    )


def test_canonical_is_long_term_by_default():
    assert is_long_term_candidate(
        MemoryType.CANONICAL,
        0.0,
    )


def test_interaction_needs_importance_threshold():
    assert not is_long_term_candidate(
        MemoryType.INTERACTION,
        0.69,
    )

    assert is_long_term_candidate(
        MemoryType.INTERACTION,
        0.7,
    )


def test_virtual_life_needs_importance_threshold():
    assert not is_long_term_candidate(
        MemoryType.VIRTUAL_LIFE,
        0.69,
    )

    assert is_long_term_candidate(
        MemoryType.VIRTUAL_LIFE,
        0.7,
    )
