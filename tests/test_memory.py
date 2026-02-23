# tests/test_memory.py
import pytest
from datetime import datetime, timedelta, timezone
from speaker.memory import (
    MemoryStore,
    InMemoryStore,
    MemoryEntry,
    MemoryKind,
    RetrievalQuery,
)


def test_memory_kind_values():
    assert MemoryKind.EPISODIC.value == "episodic"
    assert MemoryKind.SEMANTIC.value == "semantic"
    assert MemoryKind.PROCEDURAL.value == "procedural"


@pytest.mark.asyncio
async def test_store_and_retrieve_episodic():
    store = InMemoryStore()
    entry = MemoryEntry(
        kind=MemoryKind.EPISODIC,
        content={"task": "search", "result": "found 3 items", "outcome": "success"},
        tags=["search", "api"],
    )
    await store.save(entry)
    results = await store.retrieve(RetrievalQuery(query="search api", top_k=5))
    assert len(results) >= 1
    assert results[0].entry.content["task"] == "search"


@pytest.mark.asyncio
async def test_store_and_retrieve_semantic():
    store = InMemoryStore()
    entry = MemoryEntry(
        kind=MemoryKind.SEMANTIC,
        content="The customer's name is Alice and she prefers email.",
        tags=["customer", "alice"],
    )
    await store.save(entry)
    results = await store.retrieve(
        RetrievalQuery(query="alice", kind_filter=MemoryKind.SEMANTIC, top_k=5),
    )
    assert len(results) == 1


@pytest.mark.asyncio
async def test_store_and_retrieve_procedural():
    store = InMemoryStore()
    entry = MemoryEntry(
        kind=MemoryKind.PROCEDURAL,
        content={"pattern": "search → filter → summarize", "success_count": 5},
        tags=["search", "workflow"],
    )
    await store.save(entry)
    results = await store.retrieve(
        RetrievalQuery(query="search workflow", kind_filter=MemoryKind.PROCEDURAL, top_k=5),
    )
    assert len(results) == 1


@pytest.mark.asyncio
async def test_recency_boost():
    """More recent memories should rank higher, all else being equal."""
    store = InMemoryStore()
    old = MemoryEntry(
        kind=MemoryKind.EPISODIC,
        content="old search result",
        tags=["search"],
        created_at=datetime.now(tz=timezone.utc) - timedelta(days=30),
    )
    new = MemoryEntry(
        kind=MemoryKind.EPISODIC,
        content="new search result",
        tags=["search"],
    )
    await store.save(old)
    await store.save(new)
    results = await store.retrieve(RetrievalQuery(query="search", top_k=2))
    assert len(results) == 2
    # New memory should have higher activation
    assert results[0].activation >= results[1].activation


@pytest.mark.asyncio
async def test_frequency_boost():
    """More frequently accessed memories should rank higher."""
    store = InMemoryStore()
    entry = MemoryEntry(
        kind=MemoryKind.EPISODIC,
        content="frequently used",
        tags=["common"],
    )
    await store.save(entry)
    # Access it multiple times
    for _ in range(5):
        await store.retrieve(RetrievalQuery(query="common", top_k=1))
    results = await store.retrieve(RetrievalQuery(query="common", top_k=1))
    assert results[0].activation > 0.0


@pytest.mark.asyncio
async def test_empty_store():
    store = InMemoryStore()
    results = await store.retrieve(RetrievalQuery(query="anything", top_k=5))
    assert results == []
