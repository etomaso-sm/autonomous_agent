"""Long-term memory system with ACT-R activation-based retrieval."""

from __future__ import annotations

import abc
import enum
import math
import uuid
from datetime import datetime, timedelta
from typing import Any

from pydantic import BaseModel, Field


class MemoryKind(str, enum.Enum):
    EPISODIC = "episodic"
    SEMANTIC = "semantic"
    PROCEDURAL = "procedural"


class MemoryEntry(BaseModel):
    """A single memory in long-term storage."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    kind: MemoryKind
    content: Any
    tags: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    access_times: list[datetime] = Field(default_factory=list)


class RetrievalResult(BaseModel):
    """A memory with its computed activation score."""
    entry: MemoryEntry
    activation: float
    relevance: float


class RetrievalQuery(BaseModel):
    """Parameters for memory retrieval."""
    query: str
    kind_filter: MemoryKind | None = None
    top_k: int = 5
    context_tags: list[str] = Field(default_factory=list)


class MemoryStore(abc.ABC):
    """Abstract interface for long-term memory storage."""

    @abc.abstractmethod
    async def save(self, entry: MemoryEntry) -> None: ...

    @abc.abstractmethod
    async def retrieve(self, query: RetrievalQuery) -> list[RetrievalResult]: ...


class InMemoryStore(MemoryStore):
    """In-memory implementation with ACT-R activation-based retrieval.

    Activation = base_level (recency + frequency) + context_boost + noise
    Base level: ln(Σ t_j^{-d}) where t_j = time since j-th access, d = 0.5
    """

    DECAY = 0.5  # ACT-R decay parameter

    def __init__(self) -> None:
        self._entries: list[MemoryEntry] = []

    async def save(self, entry: MemoryEntry) -> None:
        self._entries.append(entry)

    async def retrieve(self, query: RetrievalQuery) -> list[RetrievalResult]:
        if not self._entries:
            return []

        now = datetime.utcnow()
        query_tokens = set(query.query.lower().split())
        results: list[RetrievalResult] = []

        for entry in self._entries:
            # Filter by kind if requested
            if query.kind_filter and entry.kind != query.kind_filter:
                continue

            # Compute base-level activation (recency + frequency)
            base_level = self._base_level_activation(entry, now)

            # Compute context boost (tag overlap)
            entry_tokens = set(t.lower() for t in entry.tags)
            content_str = str(entry.content).lower()
            content_tokens = set(content_str.split())
            all_entry_tokens = entry_tokens | content_tokens

            overlap = len(query_tokens & all_entry_tokens)
            context_boost = overlap * 0.5 if overlap > 0 else -1.0

            activation = base_level + context_boost

            if activation > -10.0:  # Threshold to avoid retrieving irrelevant memories
                relevance = overlap / max(len(query_tokens), 1)
                results.append(RetrievalResult(
                    entry=entry,
                    activation=activation,
                    relevance=relevance,
                ))

            # Record this access for frequency tracking
            entry.access_times.append(now)

        # Sort by activation (highest first), return top_k
        results.sort(key=lambda r: r.activation, reverse=True)
        return results[: query.top_k]

    def _base_level_activation(self, entry: MemoryEntry, now: datetime) -> float:
        """ACT-R base-level activation: ln(Σ t_j^{-d})"""
        access_times = entry.access_times or [entry.created_at]
        total = 0.0
        for access_time in access_times:
            elapsed = (now - access_time).total_seconds()
            elapsed = max(elapsed, 1.0)  # Avoid log(0) / division issues
            total += elapsed ** (-self.DECAY)
        if total <= 0:
            return -10.0
        return math.log(total)
