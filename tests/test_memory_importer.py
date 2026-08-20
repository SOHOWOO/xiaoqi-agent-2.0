from core.memory import MemoryStore
from core.memory.importer import CanonicalMemoryImporter
from core.memory.models import MemorySource, MemoryType


IDENTITY_FILE = "memories/canonical/identity.md.docx"


def test_canonical_importer_imports_identity():
    store = MemoryStore()
    importer = CanonicalMemoryImporter(store)

    records = importer.import_file(IDENTITY_FILE)

    assert len(records) == 23
    assert len(store) == 23

    first = records[0]

    assert first.memory_type == MemoryType.CANONICAL
    assert first.source == MemorySource.USER_PROVIDED
    assert first.content == "姓名：小七"
    assert first.importance == 1.0
    assert first.confidence == 1.0


def test_canonical_importer_skips_needs_review():
    store = MemoryStore()
    importer = CanonicalMemoryImporter(store)

    records = importer.import_file(IDENTITY_FILE)

    contents = [record.content for record in records]

    assert not any(
        "NEEDS_REVIEW" in content
        for content in contents
    )


def test_canonical_importer_generates_stable_memory_ids():
    store = MemoryStore()
    importer = CanonicalMemoryImporter(store)

    records = importer.import_file(IDENTITY_FILE)

    ids = [record.memory_id for record in records]

    assert len(ids) == len(set(ids))
    assert all(
        memory_id.startswith("canonical:identity.md:paragraph:")
        for memory_id in ids
    )


def test_canonical_importer_imports_all_memory_files():
    from pathlib import Path

    store = MemoryStore()
    importer = CanonicalMemoryImporter(store)

    files = sorted(
        Path("memories/canonical").glob("*.docx")
    )

    assert len(files) == 7

    records = importer.import_files(files)

    assert len(records) > 0
    assert len(store) == len(records)

    assert all(
        record.memory_type == MemoryType.CANONICAL
        for record in records
    )

    assert all(
        record.source == MemorySource.USER_PROVIDED
        for record in records
    )


def test_canonical_importer_is_idempotent():
    store = MemoryStore()
    importer = CanonicalMemoryImporter(store)

    path = "memories/canonical/identity.md.docx"

    first = importer.import_file(path)
    second = importer.import_file(path)

    assert len(first) == 23
    assert len(second) == 0
    assert len(store) == 23
