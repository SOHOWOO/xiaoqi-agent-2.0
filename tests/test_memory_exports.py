from core.memory import (
    MemoryAction,
    MemoryContext,
    MemoryContextBuilder,
    MemoryDecision,
    MemoryManager,
    MemoryRecord,
    MemoryRetriever,
    MemorySource,
    MemoryStore,
    MemoryType,
)


def test_memory_public_api_exports_core_components():
    assert MemoryRecord is not None
    assert MemorySource is not None
    assert MemoryType is not None
    assert MemoryStore is not None
    assert MemoryRetriever is not None
    assert MemoryContext is not None
    assert MemoryContextBuilder is not None
    assert MemoryAction is not None
    assert MemoryDecision is not None
    assert MemoryManager is not None